# Canvas LMS Control Panel

A web application to manage Canvas LMS courses and assignments through the Canvas API.

## Features

- List all courses where you are enrolled as a teacher
- View all assignments (exercises) for each course
- Modern, responsive UI built with Flask, Tailwind CSS, and Alpine.js

## Prerequisites

- Python 3.8 or higher
- Canvas LMS instance with API access
- Canvas API token with appropriate permissions

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd canvas-lms-control
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your Canvas LMS settings:
   ```
   SECRET_KEY=your-secret-key-here
   FLASK_ENV=development
   LMS_API_URL=https://your-canvas-instance.com/api/v1
   LMS_API_TOKEN=your-canvas-api-token
   ```

   To get your Canvas API token:
   1. Log in to Canvas
   2. Go to Account > Settings
   3. Scroll down to "Approved Integrations"
   4. Click "New Access Token"
   5. Copy the generated token

## Running the Application

Start the application with:
```
python app.py
```

Then open your browser and navigate to `http://localhost:5000`.

## Extending the Application

### Adding New API Endpoints

1. Add new methods to the `LMSClient` class in `api/lms_client.py`
2. Create new Flask routes in `app.py` that use these methods
3. Update the frontend templates to consume these endpoints

### Canvas API Documentation

For more information on the Canvas LMS API, see:
- [Canvas LMS API Documentation](https://canvas.instructure.com/doc/api/)

## License

This project is licensed under the MIT License - see the LICENSE file for details.