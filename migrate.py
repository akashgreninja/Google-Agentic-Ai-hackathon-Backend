import firebase_admin
from firebase_admin import credentials, firestore

# Init Source Firebase
cred_old = credentials.Certificate("firebasekey.json")
firebase_admin.initialize_app(cred_old, name="source")
source_db = firestore.client(firebase_admin.get_app("source"))

# Init Target Firebase
cred_new = credentials.Certificate("second.json")
firebase_admin.initialize_app(cred_new, name="target")
target_db = firestore.client(firebase_admin.get_app("target"))

# Migration logic
def migrate_collection(path):
    print(f"Migrating collection: {path}")
    docs = list(source_db.collection(path).stream())
    print(f"Found {len(docs)} documents in {path}")
    for doc in docs:
        data = doc.to_dict()
        target_db.collection(path).document(doc.id).set(data)
        print(f"✓ Migrated: {doc.id}")

# Run migration
migrate_collection("users")
