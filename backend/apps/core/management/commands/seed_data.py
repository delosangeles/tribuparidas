import io

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from PIL import Image, ImageDraw, ImageFont

from apps.businesses.models import Business, BusinessImage
from apps.categories.models import Category
from apps.products.models import Product
from apps.questions.models import Answer, Question
from apps.reviews.models import Review
from apps.users.models import User

CATEGORIES = [
    ("Repostería", "Postres y dulces hechos a mano.", "#F05A83"),
    ("Moda", "Ropa y accesorios con estilo propio.", "#D8446C"),
    ("Belleza", "Cuidado personal y cosmética artesanal.", "#F08FA8"),
    ("Artesanías", "Piezas únicas hechas a mano.", "#C77B96"),
    ("Comida", "Sabores caseros y comida preparada.", "#E76F8E"),
    ("Hogar", "Decoración y productos para el hogar.", "#B96580"),
    ("Servicios", "Servicios profesionales y personalizados.", "#8C5A6B"),
]

VISITORS = [
    ("maria@example.com", "María", "González"),
    ("laura@example.com", "Laura", "Ramírez"),
    ("carolina@example.com", "Carolina", "Rojas"),
]

BUSINESSES = [
    {
        "email": "stephania@tribuparidas.com",
        "name": "Dulces de Stephania",
        "category": "Repostería",
        "city": "Palmira",
        "department": "Valle del Cauca",
        "whatsapp": "+57 300 123 4567",
        "instagram": "dulcesdestephania",
        "description": (
            "En Dulces de Stephania encontrarás postres hechos con ingredientes de "
            "calidad, mucho amor y dedicación. Nos especializamos en repostería "
            "artesanal para toda ocasión."
        ),
        "products": [("Torta de chocolate", 45000), ("Cheesecake de frutos rojos", 40000), ("Cupcakes surtidos", 30000)],
        "question": "¿Hacen pedidos personalizados para cumpleaños?",
        "answer": "¡Hola! Sí, claro. Podemos personalizar el diseño, sabor y tamaño según lo que necesites.",
    },
    {
        "email": "lunaysol@tribuparidas.com",
        "name": "Luna & Sol",
        "category": "Moda",
        "city": "Cali",
        "department": "Valle del Cauca",
        "whatsapp": "+57 301 234 5678",
        "instagram": "lunaysol.moda",
        "description": "Ropa y accesorios diseñados y confeccionados a mano, con telas locales y mucho cariño.",
        "products": [("Blusa artesanal", 65000), ("Aretes tejidos", 25000)],
        "question": "¿Manejan tallas grandes?",
        "answer": "Sí, manejamos desde la talla S hasta la XXL en la mayoría de nuestras prendas.",
    },
    {
        "email": "velaviva@tribuparidas.com",
        "name": "Vela Viva",
        "category": "Artesanías",
        "city": "Palmira",
        "department": "Valle del Cauca",
        "whatsapp": "+57 302 345 6789",
        "instagram": "velaviva",
        "description": "Velas artesanales de cera de soya, hechas a mano con aromas naturales.",
        "products": [("Vela aromática grande", 38000), ("Set de velas mini", 32000)],
        "question": "¿Los aromas son naturales?",
        "answer": "Sí, usamos esencias naturales y cera de soya libre de químicos agresivos.",
    },
    {
        "email": "verdehogar@tribuparidas.com",
        "name": "Verde Hogar",
        "category": "Hogar",
        "city": "Yumbo",
        "department": "Valle del Cauca",
        "whatsapp": "+57 303 456 7890",
        "instagram": "verdehogar",
        "description": "Plantas y decoración para llenar tu hogar de vida y color.",
        "products": [("Matera de barro", 28000), ("Kit de suculentas", 45000)],
        "question": "¿Hacen envíos a Cali?",
        "answer": "Sí, hacemos envíos a Cali y alrededores con costo adicional según la zona.",
    },
    {
        "email": "manosquecrean@tribuparidas.com",
        "name": "Manos que crean",
        "category": "Artesanías",
        "city": "Cali",
        "department": "Valle del Cauca",
        "whatsapp": "+57 304 567 8901",
        "instagram": "manosquecrean",
        "description": "Artesanías en macramé, madera y fibras naturales, hechas por un colectivo de mujeres emprendedoras.",
        "products": [("Macramé decorativo", 55000), ("Cesta tejida", 42000)],
        "question": "¿Tienen tienda física?",
        "answer": "Por ahora trabajamos solo bajo pedido y ferias locales, pero puedes ver el catálogo completo aquí.",
    },
]


def make_placeholder_image(text, size, bg_hex):
    image = Image.new("RGB", size, bg_hex)
    draw = ImageDraw.Draw(image)
    font_size = max(16, size[0] // 10)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
    except OSError:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size[0] - text_w) / 2, (size[1] - text_h) / 2), text, font=font, fill="#FFFFFF")

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=85)
    return ContentFile(buffer.getvalue())


def initials(name):
    words = name.split()
    return "".join(w[0] for w in words[:2]).upper()


class Command(BaseCommand):
    help = "Carga categorías, emprendimientos, productos, preguntas y opiniones de ejemplo (idempotente)."

    @transaction.atomic
    def handle(self, *args, **options):
        categories = self._seed_categories()
        visitors = self._seed_visitors()
        self._seed_businesses(categories, visitors)
        self.stdout.write(self.style.SUCCESS("Datos de ejemplo cargados correctamente."))

    def _seed_categories(self):
        categories = {}
        for name, description, color in CATEGORIES:
            category, created = Category.objects.get_or_create(
                name=name, defaults={"description": description}
            )
            if created:
                category.image.save(f"{category.slug}.jpg", make_placeholder_image(name, (300, 300), color), save=True)
                self.stdout.write(f"Categoría creada: {name}")
            categories[name] = category
        return categories

    def _seed_visitors(self):
        visitors = []
        for email, first_name, last_name in VISITORS:
            user, created = User.objects.get_or_create(
                email=email, defaults={"first_name": first_name, "last_name": last_name}
            )
            if created:
                user.set_password("ClaveSegura123")
                user.save()
                self.stdout.write(f"Visitante creado: {email}")
            visitors.append(user)
        return visitors

    def _seed_businesses(self, categories, visitors):
        for index, data in enumerate(BUSINESSES):
            owner, created = User.objects.get_or_create(
                email=data["email"],
                defaults={"first_name": data["name"].split()[0], "last_name": "Emprendedora"},
            )
            if created:
                owner.set_password("ClaveSegura123")
                owner.save()

            business, created = Business.objects.get_or_create(
                name=data["name"],
                defaults={
                    "owner": owner,
                    "category": categories[data["category"]],
                    "city": data["city"],
                    "department": data["department"],
                    "description": data["description"],
                    "whatsapp": data["whatsapp"],
                    "instagram": data["instagram"],
                    "opening_hours": "Lun-Sáb 9am-6pm",
                    "status": Business.Status.APPROVED,
                },
            )
            if not created:
                continue

            self.stdout.write(f"Emprendimiento creado: {business.name}")
            color = CATEGORIES[[c[0] for c in CATEGORIES].index(data["category"])][2]
            business.logo.save(
                f"{business.slug}-logo.jpg", make_placeholder_image(initials(business.name), (300, 300), color), save=False
            )
            business.cover_image.save(
                f"{business.slug}-cover.jpg", make_placeholder_image(business.name, (1200, 600), color), save=False
            )
            business.save()

            for i in range(3):
                gallery_image = BusinessImage(business=business, order=i)
                gallery_image.image.save(
                    f"{business.slug}-gallery-{i + 1}.jpg",
                    make_placeholder_image(f"{business.name} {i + 1}", (600, 600), color),
                    save=True,
                )

            for product_name, price in data["products"]:
                product = Product.objects.create(
                    business=business,
                    name=product_name,
                    description=f"{product_name} de {business.name}, hecho a mano con ingredientes/materiales de calidad.",
                    price=price,
                )
                product.image.save(
                    f"{product.slug}.jpg", make_placeholder_image(product_name, (500, 500), color), save=True
                )

            asker = visitors[index % len(visitors)]
            question = Question.objects.create(business=business, user=asker, question=data["question"])
            Answer.objects.create(question=question, user=owner, answer=data["answer"])

            for offset, visitor in enumerate(visitors):
                if visitor == asker and offset == 0:
                    continue
                Review.objects.get_or_create(
                    business=business,
                    user=visitor,
                    defaults={"rating": 4 + (offset % 2), "comment": "¡Excelente atención y calidad!"},
                )
