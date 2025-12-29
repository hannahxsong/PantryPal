Pantry Pal is a full-stack web application designed to eliminate food waste by generating recipe ideas based on the ingredients already in your kitchen. Powered by the Spoonacular API, the app provides a personalized cooking experience tailored to your pantry's contents.

## Key Features
- **Smart Search Logic**: Supports complex "AND" and "OR" ingredient searches, including a custom exclusion feature (using #) to filter out unwanted items.

- **Personalized Accounts**: Secure user authentication allows users to save and manage a collection of favorite recipes.

- **Dynamic Recipe Details**: Interactive recipe pages with nutrician info, step-by-step instructions, and auto-adjusting serving sizes.

- **Global Accessibility**: Seamlessly toggle between US and Metric units for all ingredient measurements.

## Tech Stack

| Layer	| Technology |
| :--- | :--- |
| **Backend** | Python, Flask |
| **Database** | SQLAlchemy (ORM), SQLite |
| **Frontend** | Jinja2, JavaScript, CSS |
| **API** | Spoonacular Food API |

## Setup & Installation

Required: **Python 3.10 or higher** and **A Spoonacular API key** - You can get a free one at https://spoonacular.com/food-api (the free tier gives you 150 requests per day, which is plenty for testing)

1. **Clone the Repo**: git clone https://github.com/hannahxsong/PantryPal.git
2.  **Environment**: Create a virtual environment and install dependencies via `pip install -r requirements.txt.nstall -r requirements.txt`.
3.   *API Configuration**: Create a .env file and add your `SPOONACULAR_API_KEY` and a `SECRET_KEY` in `app.py`. For the SECRET_KEY, just make up a long random string (it's used for session security). For the SPOONACULAR_API_KEY, paste the key you got from Spoonacular's website.
4. **Run**: Launch the server using `flask run` or `python app.py`.

## Usage & Workflow

1. **Search**: Enter ingredients separated by commas. Use `#` before an ingredient (e.g., `#onions`) to exclude it from results.

2. **Filter**: Toggle between **AND** (must have all) and **OR** (contains any) search types for flexible discovery.

3. **Save**: Use the "Favorite" button on any recipe to store it in your personal profile.

4. **Customize**: Toggle units (Metric/US) or adjust serving sizes dynamically on the recipe details page.

## Troubleshooting

**API Connection**: Ensure your `.env` file is in the root directory and your Spoonacular key is valid.

**Database Reset**: If you encounter schema errors, you can safely delete `app.db` and restart the app to re-initialize the SQLAlchemy models.

**POST Conflict**: If the default port is busy, run the app on an alternate port using `flask run --port 5001`.
   
**Empty Results**: The app includes fallback logic for missing images or exact ingredient matches to ensure a consistent UI experience.

## Project Structure

Here's what's in the project folder:

```
PantryPal/
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
