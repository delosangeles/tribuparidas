import io

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from PIL import Image, ImageDraw, ImageFont

from apps.businesses.models import Business, BusinessImage
from apps.categories.models import Category
from apps.questions.models import Answer, Question
from apps.reviews.models import Review
from apps.users.models import User

CATEGORIES = [
    ("Repostería", "Postres y dulces hechos a mano.", "#C9A35A"),
    ("Moda", "Ropa y accesorios con estilo propio.", "#A9803C"),
    ("Belleza", "Cuidado personal y cosmética artesanal.", "#DCC1B2"),
    ("Artesanías", "Piezas únicas hechas a mano.", "#CBB8AB"),
    ("Comida", "Sabores caseros y comida preparada.", "#E8CF9D"),
    ("Hogar", "Decoración y productos para el hogar.", "#B08A5E"),
    ("Servicios", "Servicios profesionales y personalizados.", "#8A7A66"),
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
        "question": "¿Hacen pedidos personalizados para cumpleaños?",
        "answer": "¡Hola! Sí, claro. Podemos personalizar el diseño, sabor y tamaño según lo que necesites.",
        "home_delivery": True,
        "tribe_benefit": True,
        "benefit_type": Business.BenefitType.DESCUENTO,
        "benefit_detail": "10% de descuento para mamás de la tribu presentando el código TRIBU10.",
        "is_mama_tribu": True,
        "responsible_name": "Stephania Gómez",
        "tribe_recommended": True,
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
        "question": "¿Manejan tallas grandes?",
        "answer": "Sí, manejamos desde la talla S hasta la XXL en la mayoría de nuestras prendas.",
        "home_delivery": False,
        "tribe_benefit": True,
        "benefit_type": Business.BenefitType.ENVIO_GRATIS,
        "benefit_detail": "Envío gratis en compras superiores a $80.000 para mamás de la tribu.",
        "is_mama_tribu": True,
        "responsible_name": "Luna Ramírez",
        "tribe_recommended": False,
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
        "question": "¿Los aromas son naturales?",
        "answer": "Sí, usamos esencias naturales y cera de soya libre de químicos agresivos.",
        "home_delivery": True,
        "tribe_benefit": False,
        "benefit_type": "",
        "benefit_detail": "",
        "is_mama_tribu": False,
        "responsible_name": "Valentina Ríos",
        "tribe_recommended": True,
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
        "question": "¿Hacen envíos a Cali?",
        "answer": "Sí, hacemos envíos a Cali y alrededores con costo adicional según la zona.",
        "home_delivery": True,
        "tribe_benefit": True,
        "benefit_type": Business.BenefitType.PRECIO_ESPECIAL,
        "benefit_detail": "Precio especial en kits de suculentas para mamás de la tribu.",
        "is_mama_tribu": False,
        "responsible_name": "Camila Torres",
        "tribe_recommended": False,
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
        "question": "¿Tienen tienda física?",
        "answer": "Por ahora trabajamos solo bajo pedido y ferias locales, pero puedes ver el catálogo completo aquí.",
        "home_delivery": False,
        "tribe_benefit": True,
        "benefit_type": Business.BenefitType.BENEFICIO_EXCLUSIVO,
        "benefit_detail": "Taller gratuito de macramé para las primeras 5 mamás de la tribu que agenden cita.",
        "is_mama_tribu": True,
        "responsible_name": "Manuela Ospina",
        "tribe_recommended": True,
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
    help = "Carga categorías, emprendimientos, preguntas y opiniones de ejemplo (idempotente)."

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
                    "home_delivery": data["home_delivery"],
                    "tribe_benefit": data["tribe_benefit"],
                    "benefit_type": data["benefit_type"],
                    "benefit_detail": data["benefit_detail"],
                    "is_mama_tribu": data["is_mama_tribu"],
                    "responsible_name": data["responsible_name"],
                    "tribe_recommended": data["tribe_recommended"],
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
