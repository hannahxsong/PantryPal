# Design Document: Pantry Pal

## Architecture

The app follows a pretty standard Flask structure:

- **Models**: SQLAlchemy classes (`User` and `Favorite`) that define the database tables
- **Views**: Jinja2 templates in the `templates/` folder that render HTML
- **Controllers**: Route functions in `app.py` that handle requests and return responses

I kept it simple and organized - all the main logic is in `app.py`, templates are in `templates/`, and styling is in `static/style.css`.

## Database Design

I used SQLAlchemy to create two tables:

**users table**:
- `id`: Primary key (auto-incrementing integer)
- `email`: Unique email address, used for login
- `password_hash`: Hashed password (using Werkzeug's password hashing - never store plain text passwords!)

**favorites table**:
- `id`: Primary key
- `user_id`: Foreign key linking to users table
- `recipe_id`: The Spoonacular recipe ID (I don't store the full recipe in my database, just the ID)
- `recipe_title` and `recipe_image`: I cache these so I can display favorites quickly without calling the API every time

The relationship is one-to-many (one user can have many favorites). I used a foreign key constraint to make sure data stays consistent.

## Authentication

I implemented user authentication using Flask-Login, which handles sessions automatically. The `User` model needs to implement certain methods (`is_authenticated`, `is_active`, `is_anonymous`, `get_id`) that Flask-Login uses to track who's logged in.

For passwords, I hash them using Werkzeug's `generate_password_hash` before storing in the database, and verify them with `check_password_hash` on login. This is important for security - I learned from CS50 that you should never store passwords in plain text.

## API Integration

The app makes HTTP requests to the Spoonacular API using Python's `requests` library. I learned about API integration from CS50's finance problem set and applied similar patterns here.

The main endpoints I use are:
- `findByIngredients`: For OR searches and fallback recommendations
- `complexSearch`: For AND searches with filters
- `/recipes/{id}/information`: Get full recipe details with nutrition info
- `/recipes/{id}/similar`: Get similar recipes

I handle API errors with try-except blocks so the app doesn't crash if the API is down or returns an error.

## Search Functionality

The search feature was probably the most complex part to implement. Here's how it works:

**AND Search** (default): This one was straightforward - I use the `complexSearch` endpoint with the `includeIngredients` parameter. This ensures all specified ingredients are in the recipe.

**OR Search**: This was trickier. The Spoonacular API's `complexSearch` doesn't really support true OR searches well. I found a solution on Stack Overflow that suggested searching each ingredient individually and combining the results. So my OR search:
1. Loops through each ingredient
2. Searches for recipes containing that ingredient using `findByIngredients`
3. Combines all results in a dictionary (using recipe ID as key to avoid duplicates)
4. Tracks how many ingredients each recipe matches
5. Sorts by match count (recipes matching more ingredients appear first)
6. Applies filters after fetching full recipe info

This approach works well and gives users recipes sorted by relevance.

**Fallback Recommendations**: When no exact matches are found, I use the same OR search logic but present it as "recipes that share at least one ingredient." This way users still get helpful suggestions even when their exact search fails.

**Excluding Ingredients**: Users can prefix ingredients with `#` to exclude them. I filter these out before sending the search to the API. This was a simple feature to add but makes the search more flexible.

## Recipe Display

When a user searches, all matching recipes are displayed at once in a grid layout (3 recipes per row). I store all the recipes in `session["all_recipes"]` so the search state persists if the user navigates away and comes back.

The total number of recipes found is displayed at the bottom of the results. Recipes are displayed in a responsive grid that automatically adjusts to show 3 recipes per row on larger screens.

Using sessions for this means:
- All recipe data is stored server-side (more secure)
- Users can navigate away and come back without losing search results
- No need to re-query the API when returning to the search page

## Recipe Detail Page

The recipe detail page shows a lot of information, so I organized it into clear sections:

- **Overview**: Description, cuisine, source
- **Key Stats**: Time, calories, protein, fat, servings, cost
- **Dietary Tags**: Gluten-free, vegetarian, etc. as colored pill badges
- **Popularity**: Aggregate likes and Spoonacular score
- **Ingredients**: List with serving size adjustment
- **Instructions**: Numbered steps
- **Nutrition**: Common nutrients by default, with "Show All" toggle
- **Similar Recipes**: Horizontal scrollable section

**Serving Size Adjustment**: This was fun to implement. JavaScript calculates the ratio between current and original servings, then multiplies all ingredient amounts and nutrition values by that ratio. I also had to format the numbers to remove unnecessary decimals (like turning "2.00" into "2").

**Measurement Toggle**: Each ingredient stores both US and metric amounts/units in HTML data attributes. When toggling, JavaScript updates the displayed values. This was a bit tricky because not all recipes have metric conversions, so I had to handle cases where metric data might be missing.

**Nutrition Toggle**: I show common nutrients by default (carbohydrates, fiber, sugar, sodium, etc.) and hide the rest. Users can click "Show All" to see everything. This makes the page less overwhelming while still providing access to all the data.

## Similar Recipes with Common Ingredients

I wanted to show which ingredients similar recipes share with the current recipe. To do this:
1. Get the current recipe's ingredient names (lowercased for comparison)
2. For each similar recipe, fetch its full information
3. Compare ingredient name sets using Python's set intersection (`&`)
4. Store up to 3 common ingredients per similar recipe
5. Display them on the similar recipe cards

If the similar recipes endpoint fails, I have a fallback that searches by the first word of the recipe title. This ensures users always see some suggestions.

## Frontend Design

I designed the UI to be clean and modern. I was inspired by Apple, Notion, and Airbnb's design - lots of whitespace, soft shadows, rounded corners, and a neutral color palette with purple as the accent color.

The CSS uses CSS variables for consistent theming, which makes it easy to change colors throughout the site. Everything is responsive for mobile devices using media queries.

## Form Handling

I used WTForms for form validation, which I learned about from Flask documentation. The forms validate:
- Email format
- Password length (minimum 6 characters)
- Password confirmation matching
- Required fields

Form errors are displayed inline below each field, which gives users immediate feedback.

## AJAX Endpoints

I created several AJAX endpoints for dynamic functionality without page reloads:
- `/recipes/more`: Legacy endpoint (not currently used, but kept for potential future use)
- `/favorite/add/<id>`: Add recipe to favorites
- `/favorite/remove/<id>`: Remove recipe from favorites

These return JSON responses that JavaScript processes to update the UI. I learned about AJAX from CS50's finance problem set and applied it here.

## Error Handling

I used try-except blocks throughout to handle API errors gracefully. If an API call fails, the app shows a user-friendly error message instead of crashing. For similar recipes, if the main endpoint fails, it tries a fallback search.

## Security

I made sure to:
- Hash passwords before storage (never plain text)
- Use SQLAlchemy's query methods to prevent SQL injection (parameterized queries)
- Store API keys in environment variables, not in code
- Use Flask-Login for secure session management

## Performance

To keep things fast:
- Recipe data is cached in session to avoid repeated API calls
- All recipes are displayed at once in a grid layout
- Database queries use indexes (primary keys and foreign keys)

## Challenges I Faced

1. **OR Search Problem**: The Spoonacular API's `complexSearch` doesn't handle OR searches well. I found a solution on Stack Overflow that searches each ingredient separately and combines results.

2. **Ingredient Amount Formatting**: Removing unnecessary decimals was trickier than I thought. I ended up creating a JavaScript function that formats numbers and removes trailing zeros.

3. **Measurement Conversion**: Not all recipes have metric data. I store both US and metric in data attributes and use US as fallback if metric is missing.

4. **Similar Recipes Images**: Some recipes don't have images in the similar endpoint response. I fetch full recipe info for each similar recipe to get images, with a fallback to a default image URL.

5. **Session Management**: I needed to store recipe data between requests so users could navigate away and return without losing their search results. Flask sessions worked perfectly for this.

## What I Learned

This project taught me a lot:
- How to integrate with external APIs (Spoonacular)
- How to handle different search types (AND vs OR)
- How to manage session state for maintaining search results
- How to make dynamic, interactive web pages with JavaScript
- How to design a clean, modern UI
- How to handle errors gracefully

I used concepts from CS50 lectures (Flask, SQL, web development) and learned new things from documentation and Stack Overflow when I got stuck.

## Future Improvements

If I had more time, I'd add:
- Recipe ratings and reviews
- Meal planning (save recipes to specific days)
- Shopping list generation from recipes
- Better caching to reduce API calls
- User recipe uploads
- Recipe sharing between users

## References

- Flask Documentation: https://flask.palletsprojects.com/
- SQLAlchemy Documentation: https://docs.sqlalchemy.org/
- Flask-Login Documentation: https://flask-login.readthedocs.io/
- Spoonacular API Documentation: https://spoonacular.com/food-api/docs
- CS50 Lectures (Weeks 7-9 on Flask, SQL, and web development)
- Stack Overflow discussions on OR search implementations with Spoonacular API
