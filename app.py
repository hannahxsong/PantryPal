import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session
import requests

# load environment variables from .env file (keeps api key and secret key out of code)
base_dir = Path(__file__).resolve().parent
load_dotenv(base_dir / ".env")

db_url = os.getenv("DATABASE_URL", f"sqlite:///{base_dir / 'app.db'}")
api_key = os.getenv("SPOONACULAR_API_KEY")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-me")

# database setup using sqlalchemy (learned from cs50 lectures and flask docs)
# scoped_session ensures thread-safe database access
db_engine = create_engine(db_url, echo=False)
db_session = scoped_session(sessionmaker(bind=db_engine, autoflush=False, autocommit=False))
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    # flask-login requires these methods to work properly (from flask-login documentation)
    # these tell flask-login about the user's authentication state
    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        # flask-login needs the id as a string
        return str(self.id)


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipe_id = Column(Integer, nullable=False)
    recipe_title = Column(String(500), nullable=False)
    recipe_image = Column(String(500))


Base.metadata.create_all(bind=db_engine)

# setup flask-login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# this function loads a user from the database when flask-login needs it
# it's called automatically by flask-login when checking if a user is logged in
@login_manager.user_loader
def load_user(user_id):
    db = db_session()
    try:
        return db.get(User, int(user_id))
    finally:
        db.close()


# form classes using wtforms
class SignupForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=6, message="Password must be at least 6 characters.")],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Sign Up")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log In")


class IngredientForm(FlaskForm):
    ingredients = TextAreaField(
        "What ingredients do you have?",
        validators=[DataRequired()],
        render_kw={"rows": 3, "placeholder": "eggs, milk, spinach"},
    )
    max_time = SelectField(
        "Max Time",
        choices=[
            ("", "Any"),
            ("15", "< 15 min"),
            ("30", "< 30 min"),
            ("60", "< 1 hour"),
            ("120", "< 2 hours"),
        ],
        default="",
    )
    cuisine = SelectField(
        "Cuisine",
        choices=[
            ("", "Any"),
            ("italian", "Italian"),
            ("mexican", "Mexican"),
            ("chinese", "Chinese"),
            ("indian", "Indian"),
            ("american", "American"),
            ("japanese", "Japanese"),
            ("thai", "Thai"),
            ("french", "French"),
            ("mediterranean", "Mediterranean"),
        ],
        default="",
    )
    submit = SubmitField("Find Recipes")


def get_recipes(ingredients, max_time=None, cuisine=None, num=30, search_type='AND', dish_type=None, low_ingredient=False):
    """search for recipes using spoonacular api. supports both AND and OR search types."""
    if not api_key:
        raise RuntimeError("API key not set. Add SPOONACULAR_API_KEY to .env file")
    
    # split ingredients into a list and normalize (lowercase, strip whitespace)
    ingredients_list = [ing.strip().lower() for ing in ingredients.split(',') if ing.strip()]
    
    # or search: search each ingredient separately and combine results
    # learned about this approach from stack overflow when complexSearch didn't work for OR
    if search_type == 'OR':
        # use dictionary to avoid duplicate recipes (key is recipe id)
        all_recipes = {}
        # track how many ingredients each recipe matches (for sorting)
        ingredient_match_count = {}
        
        for ingredient in ingredients_list:
            try:
                url = "https://api.spoonacular.com/recipes/findByIngredients"
                params = {
                    "apiKey": api_key,
                    "ingredients": ingredient,
                    "number": 50,  # get more results to combine
                    "ranking": 1,
                    "ignorePantry": True
                }
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                recipes = response.json()
                
                # add recipes to our collection, tracking match count
                for recipe in recipes:
                    recipe_id = recipe.get("id")
                    if recipe_id:
                        if recipe_id not in all_recipes:
                            all_recipes[recipe_id] = recipe
                            ingredient_match_count[recipe_id] = 0
                        ingredient_match_count[recipe_id] += 1
            except:
                continue
        
        # sort by number of matching ingredients (more matches first)
        # using lambda function to sort by match count
        recipes = list(all_recipes.values())
        recipes.sort(key=lambda r: ingredient_match_count.get(r.get("id", 0), 0), reverse=True)
        recipes = recipes[:num]
        
        # get full recipe info and apply filters
        recipes_with_info = []
        for recipe in recipes:
            try:
                info_url = f"https://api.spoonacular.com/recipes/{recipe['id']}/information"
                info_params = {"apiKey": api_key}
                info_response = requests.get(info_url, params=info_params, timeout=10)
                info_response.raise_for_status()
                info = info_response.json()
                recipe["readyInMinutes"] = info.get("readyInMinutes")
                recipe["cuisines"] = info.get("cuisines", [])
                recipe["image"] = info.get("image", recipe.get("image", ""))
                
                # apply filters
                if max_time and info.get("readyInMinutes", 0) > int(max_time):
                    continue
                if cuisine and cuisine not in info.get("cuisines", []):
                    continue
                if dish_type and dish_type not in info.get("dishTypes", []):
                    continue
            except:
                pass
            recipes_with_info.append(recipe)
        return recipes_with_info
    
    # and search: use complexSearch endpoint (simpler than OR since api supports it)
    url = "https://api.spoonacular.com/recipes/complexSearch"
    params = {
        "apiKey": api_key,
        "number": num,
        "addRecipeInformation": True,
        "includeIngredients": ingredients,  # this makes it an AND search
    }
    
    # add optional filters if they were provided
    if max_time:
        params["maxReadyTime"] = int(max_time)
    if cuisine:
        params["cuisine"] = cuisine
    if dish_type:
        params["type"] = dish_type
    if low_ingredient:
        params["minIngredients"] = 1
        params["maxIngredients"] = 5
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        recipes = response.json().get("results", [])
        
        # get additional info for each recipe (cooking time, cuisines, etc.)
        # complexSearch doesn't always return everything, so we fetch full details
        recipes_with_info = []
        for recipe in recipes:
            try:
                info_url = f"https://api.spoonacular.com/recipes/{recipe['id']}/information"
                info_params = {"apiKey": api_key}
                info_response = requests.get(info_url, params=info_params, timeout=10)
                info_response.raise_for_status()
                info = info_response.json()
                recipe["readyInMinutes"] = info.get("readyInMinutes")
                recipe["cuisines"] = info.get("cuisines", [])
            except:
                # if we can't get full info, just use what we have
                pass
            recipes_with_info.append(recipe)
        return recipes_with_info
    except requests.HTTPError:
        raise
    except Exception as e:
        raise RuntimeError(f"Error fetching recipes: {e}")


def get_fallback_recipes(ingredients, num=30):
    """when no exact matches found, get recipes that share at least one ingredient."""
    if not api_key:
        return []
    
    # same approach as OR search - search each ingredient and combine
    ingredients_list = [ing.strip().lower() for ing in ingredients.split(',') if ing.strip()]
    all_recipes = {}
    ingredient_match_count = {}
    
    # search each ingredient and combine results
    for ingredient in ingredients_list:
        try:
            url = "https://api.spoonacular.com/recipes/findByIngredients"
            params = {
                "apiKey": api_key,
                "ingredients": ingredient,
                "number": 50,
                "ranking": 1,
                "ignorePantry": True
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            recipes = response.json()
            
            for recipe in recipes:
                recipe_id = recipe.get("id")
                if recipe_id:
                    if recipe_id not in all_recipes:
                        all_recipes[recipe_id] = recipe
                        ingredient_match_count[recipe_id] = 0
                    ingredient_match_count[recipe_id] += 1
        except:
            continue
    
    # sort by match count (recipes with more matching ingredients first)
    recipes = list(all_recipes.values())
    recipes.sort(key=lambda r: ingredient_match_count.get(r.get("id", 0), 0), reverse=True)
    recipes = recipes[:num]
    
    # get full recipe info
    recipes_with_info = []
    for recipe in recipes:
        try:
            info_url = f"https://api.spoonacular.com/recipes/{recipe['id']}/information"
            info_params = {"apiKey": api_key}
            info_response = requests.get(info_url, params=info_params, timeout=8)
            info_response.raise_for_status()
            info = info_response.json()
            recipe["readyInMinutes"] = info.get("readyInMinutes")
            recipe["cuisines"] = info.get("cuisines", [])
            recipe["image"] = info.get("image", recipe.get("image", ""))
            recipe["match_count"] = ingredient_match_count.get(recipe.get("id", 0), 0)
        except:
            continue
        recipes_with_info.append(recipe)
    return recipes_with_info


def get_favorite_ids(user_id):
    db = db_session()
    try:
        favorites = db.query(Favorite).filter_by(user_id=user_id).all()
        return [f.recipe_id for f in favorites]
    finally:
        db.close()


def store_recipes_in_session(recipes_list):
    """store recipes in session with minimal data to avoid cookie size limits"""
    recipes_to_store = []
    for recipe in recipes_list:
        recipes_to_store.append({
            "id": recipe.get("id"),
            "title": recipe.get("title"),
            "image": recipe.get("image", ""),
            "readyInMinutes": recipe.get("readyInMinutes"),
            "cuisines": recipe.get("cuisines", []),
            "usedIngredientCount": recipe.get("usedIngredientCount"),
            "missedIngredientCount": recipe.get("missedIngredientCount"),
            "usedIngredients": recipe.get("usedIngredients", []),
            "missedIngredients": recipe.get("missedIngredients", []),
            "match_count": recipe.get("match_count")
        })
    session["all_recipes"] = recipes_to_store
    session.modified = True
    return len(recipes_to_store)  # return count for verification


@app.route("/")
def index():
    # if user is already logged in, redirect to search page
    if current_user.is_authenticated:
        return redirect(url_for("ingredients"))
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        db = db_session()
        try:
            # check if email already exists
            existing = db.query(User).filter_by(email=form.email.data.lower()).first()
            if existing:
                flash("Email already exists. Please log in.", "warning")
            else:
                # create new user with hashed password
                new_user = User(
                    email=form.email.data.lower(),  # store email in lowercase for consistency
                    password_hash=generate_password_hash(form.password.data)
                )
                db.add(new_user)
                db.commit()
                flash("Account created! You can now log in.", "success")
                return redirect(url_for("login"))
        finally:
            db.close()
    return render_template("signup.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db = db_session()
        try:
            user = db.query(User).filter_by(email=form.email.data.lower()).first()
            # verify password using hash comparison
            if user and check_password_hash(user.password_hash, form.password.data):
                login_user(user)  # flask-login handles the session
                flash("Logged in successfully!", "success")
                # redirect to page user was trying to access, or ingredients page
                next_page = request.args.get("next")
                return redirect(next_page or url_for("ingredients"))
            else:
                flash("Invalid email or password.", "danger")
        finally:
            db.close()
    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/ingredients", methods=["GET", "POST"])
@login_required
def ingredients():
    form = IngredientForm()
    recipes = None
    error = None
    favorite_ids = get_favorite_ids(current_user.id)

    # handle form submission (new search) - must check this first
    # validate_on_submit() only returns True for POST requests with valid data
    if request.method == "POST" and form.validate_on_submit():
        # clear previous search results from session
        session.pop("all_recipes", None)
        ingredients_text = form.ingredients.data
        
        # filter out ingredients prefixed with # (exclude from search)
        # this lets users exclude ingredients they don't want
        ingredients_list = [ing.strip() for ing in ingredients_text.split(',') if ing.strip() and not ing.strip().startswith('#')]
        ingredients_text = ', '.join(ingredients_list)
        
        # get form data and optional filters
        max_time = form.max_time.data if form.max_time.data else None
        cuisine = form.cuisine.data if form.cuisine.data else None
        # these aren't in the wtform, so get them from request.form directly
        search_type = request.form.get('search_type', 'AND')
        dish_type = request.form.get('dish_type', '')
        low_ingredient = request.form.get('low_ingredient', '') == 'on'
        
        # store search parameters in session so we can restore them when user returns
        session["search_params"] = {
            "ingredients": form.ingredients.data,  # store original with # prefixes
            "max_time": max_time or "",
            "cuisine": cuisine or "",
            "search_type": search_type,
            "dish_type": dish_type,
            "low_ingredient": low_ingredient
        }
        session.modified = True
        
        try:
            all_recipes = get_recipes(ingredients_text, max_time, cuisine, search_type=search_type, dish_type=dish_type, low_ingredient=low_ingredient)
            if not all_recipes:
                # fallback: show recipes that share at least one ingredient
                # this gives users helpful suggestions even when exact search fails
                fallback_recipes = get_fallback_recipes(ingredients_text, num=30)
                if fallback_recipes:
                    # store recipes in session (minimal data to avoid cookie size limits)
                    stored_count = store_recipes_in_session(fallback_recipes)
                    session["is_fallback"] = True  # mark so we can show different message
                    recipes = fallback_recipes  # show all recipes (use full data for display)
                    error = f"No exact matches found. Here are recipes that share at least one ingredient with your search:"
                else:
                    error = "No recipes found. Try different ingredients."
                    session.pop("all_recipes", None)
            else:
                # store all recipes in session and display all at once
                # store minimal data to avoid cookie size limits (4KB for Flask sessions)
                stored_count = store_recipes_in_session(all_recipes)
                session.pop("is_fallback", None)
                recipes = all_recipes  # show all recipes (use full data for display)
        except requests.HTTPError as e:
            status_code = e.response.status_code
            if status_code == 402:
                error = "API quota exceeded. The free Spoonacular API tier allows 150 requests per day. Please try again tomorrow or upgrade your API plan at https://spoonacular.com/food-api/pricing"
            elif status_code == 401:
                error = "API key is invalid. Please check your SPOONACULAR_API_KEY in the .env file."
            elif status_code == 429:
                error = "Too many requests. Please wait a moment and try again."
            else:
                error = f"Error from API: {status_code}"
        except Exception as e:
            error = f"Something went wrong: {e}"
    
    # if no form submission, check if we have recipes in session (returning from recipe detail)
    # this handles when user clicks "back to recipes" from a recipe detail page
    if recipes is None and "all_recipes" in session:
        all_recipes = session.get("all_recipes", [])
        # make sure we have a list and it's not empty
        if isinstance(all_recipes, list) and len(all_recipes) > 0:
            recipes = all_recipes  # restore all recipes from session
            if session.get("is_fallback"):
                error = "Showing recipes that share at least one ingredient with your search:"
            
            # restore search parameters from session to pre-populate form
            search_params = session.get("search_params", {})
            if search_params:
                form.ingredients.data = search_params.get("ingredients", "")
                form.max_time.data = search_params.get("max_time", "")
                form.cuisine.data = search_params.get("cuisine", "")
        else:
            # debug: if session has all_recipes but it's empty or wrong type, clear it
            session.pop("all_recipes", None)

    total_recipes = len(session.get("all_recipes", [])) if "all_recipes" in session else (len(recipes) if recipes else 0)
    # pass search params to template for non-wtform fields (dish_type, search_type, low_ingredient)
    search_params = session.get("search_params", {}) if "all_recipes" in session else {}
    return render_template("ingredients.html", form=form, recipes=recipes, error=error, favorite_ids=favorite_ids, total_recipes=total_recipes, search_params=search_params)


@app.route("/recipes/more", methods=["POST"])
@login_required
def get_more_recipes():
    """ajax endpoint to load more recipes (legacy - not currently used, but kept for potential future use)"""
    try:
        # get recipes from session (stored from initial search)
        all_recipes = session.get("all_recipes", [])
        
        if not all_recipes:
            return jsonify({"success": False, "message": "No recipes in session. Please search again."}), 400
        
        current_count = int(request.json.get("current_count", 9))
        
        # make sure current_count is valid
        if current_count >= len(all_recipes):
            return jsonify({
                "success": True,
                "recipes": [],
                "has_more": False,
                "total_recipes": len(all_recipes),
                "current_count": current_count
            })
        
        # slice to get next 9 recipes
        next_batch = all_recipes[current_count:current_count + 9]
        
        if not next_batch:
            return jsonify({
                "success": True,
                "recipes": [],
                "has_more": False,
                "total_recipes": len(all_recipes),
                "current_count": current_count
            })
        
        favorite_ids = get_favorite_ids(current_user.id)
        
        recipes_data = []
        for recipe in next_batch:
            recipes_data.append({
                "id": recipe.get("id"),
                "title": recipe.get("title"),
                "image": recipe.get("image", ""),
                "readyInMinutes": recipe.get("readyInMinutes"),
                "cuisines": recipe.get("cuisines", []),
                "usedIngredientCount": recipe.get("usedIngredientCount"),
                "missedIngredientCount": recipe.get("missedIngredientCount"),
                "usedIngredients": recipe.get("usedIngredients", []),
                "missedIngredients": recipe.get("missedIngredients", []),
                "is_favorited": recipe.get("id") in favorite_ids,
                "match_count": recipe.get("match_count")
            })
        
        # calculate if there are more recipes after this batch
        new_count = current_count + len(recipes_data)
        has_more = new_count < len(all_recipes)
        
        return jsonify({
            "success": True,
            "recipes": recipes_data,
            "has_more": has_more,
            "total_recipes": len(all_recipes),
            "current_count": new_count
        })
    except Exception as e:
        # catch any errors and return proper error response
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


@app.route("/favorites")
@login_required
def favorites():
    # get all favorites for the current user
    db = db_session()
    try:
        user_favorites = db.query(Favorite).filter_by(user_id=current_user.id).all()
        return render_template("favorites.html", favorites=user_favorites)
    finally:
        db.close()


@app.route("/profile")
@login_required
def profile():
    # show user's account info and stats
    db = db_session()
    try:
        favorite_count = db.query(Favorite).filter_by(user_id=current_user.id).count()
        return render_template("profile.html", favorite_count=favorite_count)
    finally:
        db.close()


@app.route("/favorite/add/<int:recipe_id>", methods=["POST"])
@login_required
def add_favorite(recipe_id):
    """ajax endpoint to add recipe to favorites"""
    db = db_session()
    try:
        # check if already favorited
        existing = db.query(Favorite).filter_by(user_id=current_user.id, recipe_id=recipe_id).first()
        if existing:
            return jsonify({"success": False, "message": "Already in favorites"}), 400
        
        # get recipe info from api to save title and image (so we can display without api call later)
        url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
        params = {"apiKey": api_key}
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        recipe_data = response.json()
        
        new_favorite = Favorite(
            user_id=current_user.id,
            recipe_id=recipe_id,
            recipe_title=recipe_data.get("title", "Unknown"),
            recipe_image=recipe_data.get("image", "")
        )
        db.add(new_favorite)
        db.commit()
        return jsonify({"success": True, "message": "Added to favorites"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        db.close()


@app.route("/favorite/remove/<int:recipe_id>", methods=["POST"])
@login_required
def remove_favorite(recipe_id):
    """ajax endpoint to remove recipe from favorites"""
    db = db_session()
    try:
        favorite = db.query(Favorite).filter_by(user_id=current_user.id, recipe_id=recipe_id).first()
        if favorite:
            db.delete(favorite)
            db.commit()
            return jsonify({"success": True, "message": "Removed from favorites"})
        else:
            return jsonify({"success": False, "message": "Not in favorites"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        db.close()


@app.route("/recipe/<int:recipe_id>")
@login_required
def recipe_detail(recipe_id):
    """display full recipe details with ingredients, instructions, nutrition, etc."""
    try:
        url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
        params = {
            "apiKey": api_key,
            "includeNutrition": True
        }
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        recipe = response.json()
        
        # get similar recipes with fallback if main endpoint fails
        similar_recipes = []
        try:
            similar_url = f"https://api.spoonacular.com/recipes/{recipe_id}/similar"
            similar_params = {
                "apiKey": api_key,
                "number": 5
            }
            similar_response = requests.get(similar_url, params=similar_params, timeout=10)
            similar_response.raise_for_status()
            similar_recipes = similar_response.json()
            
            # find common ingredients between current recipe and similar ones
            # using set intersection to find shared ingredients
            if similar_recipes and recipe.get("extendedIngredients"):
                # create set of current recipe's ingredient names (lowercase for comparison)
                current_ingredient_names = {ing.get("name", "").lower() for ing in recipe.get("extendedIngredients", [])}
                for similar in similar_recipes:
                    try:
                        similar_info_url = f"https://api.spoonacular.com/recipes/{similar['id']}/information"
                        similar_info_params = {"apiKey": api_key}
                        similar_info_response = requests.get(similar_info_url, params=similar_info_params, timeout=8)
                        similar_info_response.raise_for_status()
                        similar_info = similar_info_response.json()
                        similar["image"] = similar_info.get("image", "")
                        # get similar recipe's ingredients and find intersection
                        similar_ingredient_names = {ing.get("name", "").lower() for ing in similar_info.get("extendedIngredients", [])}
                        # set intersection (&) finds common elements
                        common_ingredients = list(current_ingredient_names & similar_ingredient_names)
                        similar["common_ingredients"] = common_ingredients[:3]  # limit to 3 for display
                    except:
                        similar["common_ingredients"] = []
                        if not similar.get("image"):
                            similar["image"] = f"https://spoonacular.com/recipeImages/{similar['id']}-312x231.jpg"
        except:
            # fallback: search by recipe title if similar endpoint fails
            try:
                fallback_url = "https://api.spoonacular.com/recipes/complexSearch"
                fallback_params = {
                    "apiKey": api_key,
                    "query": recipe.get("title", "").split()[0] if recipe.get("title") else "",
                    "number": 5,
                    "addRecipeInformation": True
                }
                fallback_response = requests.get(fallback_url, params=fallback_params, timeout=10)
                fallback_response.raise_for_status()
                fallback_results = fallback_response.json().get("results", [])
                similar_recipes = [r for r in fallback_results if r.get("id") != recipe_id][:5]
            except:
                pass
        
        favorite_ids = get_favorite_ids(current_user.id)
        is_favorited = recipe_id in favorite_ids
        
        return render_template("recipe_detail.html", recipe=recipe, is_favorited=is_favorited, similar_recipes=similar_recipes)
    except requests.HTTPError as e:
        flash(f"Error loading recipe: {e.response.status_code}", "danger")
        return redirect(url_for("ingredients"))
    except Exception as e:
        flash(f"Something went wrong: {e}", "danger")
        return redirect(url_for("ingredients"))


if __name__ == "__main__":
    app.run(debug=True)
