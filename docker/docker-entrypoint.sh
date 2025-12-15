#!/bin/bash
set -e

echo "🚀 Starting Primary Assistant Application..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL..."
while ! pg_isready -h "$POSTGRES_HOST" -U "$POSTGRES_USER" > /dev/null 2>&1; do
    sleep 1
done
echo "✅ PostgreSQL is ready!"

# Run database migrations
echo "🔄 Running database migrations..."
cd /app/website
flask db upgrade || {
    echo "❌ Failed to run migrations"
    exit 1
}
cd /app
echo "✅ Migrations completed successfully!"

# Create admin user if ADMIN_PASSWORD is set and user doesn't exist
if [ -n "$ADMIN_PASSWORD" ]; then
    echo "👤 Creating admin user..."
    python website/scripts/create_admin_user.py --username "${ADMIN_USERNAME:-admin}" --email "${ADMIN_EMAIL:-admin@example.com}" || {
        echo "⚠️  Admin user creation failed (may already exist)"
    }
fi

echo "🎉 Application initialization complete!"
echo "🌐 Starting web server..."

# Execute the CMD from Dockerfile (gunicorn)
exec "$@"
