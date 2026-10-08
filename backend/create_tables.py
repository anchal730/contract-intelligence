from app.database import Base, engine
from app.models.document import Document, DocumentVersion, Page


print("Creating database tables...")

Base.metadata.create_all(bind=engine)

print("Tables created successfully!")