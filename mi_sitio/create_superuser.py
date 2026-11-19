import os
from django.contrib.auth import get_user_model
from django.db.utils import OperationalError, ProgrammingError

try:
    User = get_user_model()
    password = os.environ.get("ADMIN_PASSWORD")   # se carga en Render, no queda en GitHub

    if password and not User.objects.filter(username="admin").exists():
        User.objects.create_superuser(
            username="admin",
            email="admin@mail.com",
            password=password,
        )
        print("Superusuario creado")
    else:
        print("El superusuario ya existe o no hay ADMIN_PASSWORD")

except (OperationalError, ProgrammingError):
    print("La base de datos aún no está lista. Intentá de nuevo tras migraciones.")