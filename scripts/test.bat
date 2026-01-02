docker cp /home/nathan/vitruvian-developer/scripts/import_markdown_data.py primary-assistant-web:/app/scripts/import_markdown_data.py

# Verify it has the fix
docker-compose -f docker-compose.yml -f docker-compose.remote.yml exec web grep -A 5 "Create new meal log" /app/scripts/import_markdown_data.py

# Delete the bad meals
docker-compose -f docker-compose.yml -f docker-compose.remote.yml exec web python -c "
from website.app import create_app
from website.models.nutrition import MealLog
from website.models import db
app = create_app()
with app.app_context():
    count = MealLog.query.delete()
    db.session.commit()
    print(f'Deleted {count} meals')
"

# Re-import with the correct script
docker-compose -f docker-compose.yml -f docker-compose.remote.yml exec web python /app/scripts/import_markdown_data.py
