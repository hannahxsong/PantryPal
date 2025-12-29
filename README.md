Pantry Pal is a web app I built that helps you find recipes based on what ingredients you already have in your fridge/kitchen/pantry. Instead of going to the store or wondering what to cook, just type in what you have and get recipe suggestions powered by the Spoonacular API.

## What It Does

The main idea is pretty simple: you tell the app what ingredients you have, and it finds recipes that use them. But I added some more features to make it more useful:

- **User accounts**: Sign up and log in so you can save your favorite recipes
- **Smart search**: You can search for recipes that use ALL your ingredients (AND) or ANY of them (OR)
- **Filters**: Narrow down by cooking time, cuisine type, dish type, or find simple recipes with 5 or fewer ingredients
- **Exclude ingredients**: Don't want something? Just put a # in front of it (like "#spinach") and it won't be included in the search
- **Full recipe pages**: Click any recipe to see ingredients, step-by-step instructions, nutrition info, and more
- **Adjust servings**: On recipe pages, you can change the serving size and all the ingredient amounts update automatically
- **Measurement units**: Toggle between US and metric measurements
- **Favorites**: Save recipes you like to come back to later
- **Fallback suggestions**: If no exact matches, it shows recipes that share at least one ingredient with your search

## Getting Started

### What You Need

1. **Python 3.10 or higher** - If you're using CS50 codespace, you already have this
2. **A Spoonacular API key** - You can get a free one at https://spoonacular.com/food-api (the free tier gives you 150 requests per day, which is plenty for testing)

### Installation Steps

1. **Download or clone this project** to your computer or CS50 codespace

2. **Set up a virtual environment** (this keeps dependencies organized):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # On Windows: venv\Scripts\activate
   ```
   You should see `(venv)` appear in your terminal prompt when it's activated.

3. **Install the required packages**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Create a `.env` file** in the same folder as `app.py`. This file stores your API key and secret key securely. It should look like this:
   ```
   SECRET_KEY=make-up-any-long-random-string-here
   SPOONACULAR_API_KEY=your-actual-api-key-from-spoonacular
   ```
   For the SECRET_KEY, just make up a long random string (it's used for session security). For the SPOONACULAR_API_KEY, paste the key you got from Spoonacular's website.
   
   **Important**: Don't share your `.env` file or commit it to git! It contains sensitive information.

### Running the App

1. **Make sure your virtual environment is activated** (you should see `(venv)` in your terminal)

2. **Start the Flask server**:
   ```bash
   flask --app app run
   ```
   
   Or you can run:
   ```bash
   python app.py
   ```

3. **Open your browser** and go to:
   - `http://127.0.0.1:5000` (if running locally)
   - `http://localhost:5000` (if using CS50 codespace)

## How to Use the App

### First Time Setup

1. When you first visit the site, you'll see the homepage with a "Get Started" button
2. Click "Sign Up" and create an account with your email and password
3. After signing up, you'll be redirected to log in
4. Once logged in, you'll see the recipe search page

### Searching for Recipes

The main feature is the ingredient search. Here's how it works:

1. **Type your ingredients** in the text box, separated by commas. For example: `eggs, milk, flour, butter`

2. **Choose your search type**:
   - **AND** (default): Recipes must contain ALL the ingredients you listed
   - **OR**: Recipes can contain ANY of the ingredients (useful when you have a lot of random stuff)

3. **Add filters** (all optional):
   - **Max Time**: Only show recipes that take less than a certain amount of time
   - **Cuisine**: Filter by Italian, Mexican, Chinese, etc.
   - **Dish Type**: Main course, dessert, side dish, etc.
   - **Low-ingredient**: Check this to only see recipes with 5 or fewer ingredients

4. **Exclude ingredients**: If you don't want a certain ingredient in your results, put a `#` in front of it. For example: `chicken, rice, #mushrooms` will search for chicken and rice recipes but exclude any with mushrooms.

5. **Click "Find Recipes"** and wait for results!

### Viewing Recipe Results

When you get results, you'll see:
- Recipe cards with images and titles
- How many of your ingredients each recipe uses
- Lists of which ingredients are used and which are missing
- A "View full recipe" button to see the complete recipe
- A heart button to add recipes to your favorites

All matching recipes are displayed at once in a grid layout (3 recipes per row). The total number of recipes found is shown at the bottom of the results.

### Recipe Detail Pages

When you click "View full recipe", you'll see a full page with:

- **Overview**: Description, cuisine type, and source
- **Key Stats**: Cooking time, calories, protein, fat, servings, and cost
- **Dietary Tags**: Gluten-free, vegetarian, vegan, etc. as colored badges
- **Popularity**: How many people tried it and the Spoonacular score
- **Ingredients**: Full list with amounts
  - Use the +/- buttons to adjust serving size (ingredient amounts update automatically)
  - Toggle between US and Metric measurements
- **Instructions**: Step-by-step cooking instructions
- **Nutrition Breakdown**: Common nutrients shown by default, with a "Show All" button for complete info
- **Similar Recipes**: Other recipes you might like, with indicators showing which ingredients they share

### Managing Favorites

- **Add to favorites**: Click the heart button on any recipe card or recipe detail page
- **View favorites**: Click "Favorites" in the navigation bar
- **Remove favorites**: Click the heart button again on a favorited recipe

### Your Profile

Click "Profile" in the navigation to see:
- Your email address
- Total number of favorite recipes you've saved
- Quick links to search for recipes or view favorites

## Troubleshooting

**"API key not set" error**: 
- Make sure you created the `.env` file in the same directory as `app.py`
- Check that it contains `SPOONACULAR_API_KEY=your-key-here` (no spaces around the =)
- Make sure you activated your virtual environment before running the app

**"No recipes found"**: 
- Try using more common ingredients
- Switch from AND to OR search type
- Remove some filters
- The app will automatically show fallback recommendations if no exact matches are found

**Database errors**: 
- If you see database-related errors, you can delete `app.db` and restart the app (this will reset all user data, but it's fine for testing)

**Port already in use**: 
- If port 5000 is busy, you can use a different port:
  ```bash
  flask --app app run --port 5001
  ```

**Images not loading**: 
- Some recipes might not have images from the API. The app handles this gracefully with fallback images.

## Project Structure

Here's what's in the project folder:

```
cs50 final proj/
├── app.py                 # Main Flask application (all the routes and logic)
├── app.db                 # SQLite database (created automatically when you first run)
├── .env                   # Your API keys (you create this, don't commit it!)
├── requirements.txt       # Python packages needed
├── README.md             # This file
├── DESIGN.md             # Technical details about how I built it
├── static/
│   └── style.css         # All the CSS styling
└── templates/
    ├── base.html         # Base template with navigation (other pages extend this)
    ├── index.html        # Homepage
    ├── login.html        # Login page
    ├── signup.html       # Signup page
    ├── ingredients.html  # Recipe search page (main feature)
    ├── recipe_detail.html # Full recipe view with all the details
    ├── favorites.html    # List of saved recipes
    └── profile.html      # User profile page
```

## Technologies I Used

- **Flask**: Web framework (learned in CS50 Week 9)
- **SQLAlchemy**: Database ORM (learned in CS50 Week 9)
- **Flask-Login**: Handles user sessions and authentication
- **WTForms**: Form validation (makes sure emails are valid, passwords match, etc.)
- **Spoonacular API**: Where all the recipe data comes from
- **JavaScript**: For the interactive features like serving size adjustment, measurement toggles, and favorites

## Notes

- The app uses SQLite for the database, which gets created automatically the first time you run it
- You need an internet connection since recipe data comes from the Spoonacular API
- Free Spoonacular API keys have rate limits (150 requests per day), so if you're testing/searching for recipes a lot, you might hit the limit
- All passwords are hashed before being stored (never stored in plain text - learned this is important from CS50!)
- The app stores recipe search results in Flask sessions to maintain search state
- Install all the requirements from `requirements.txt`
## More notes for user:

The app should work out of the box once you have the API key set up. If you run into issues that aren't covered here, the error messages should give you a clue about what's wrong.
