"""Base repository with common CRUD operations."""


class BaseRepository:
    model_class = None

    def __init__(self, session):
        self.session = session

    def get_by_id(self, entity_id):
        return self.session.get(self.model_class, entity_id)

    def create(self, attrs: dict):
        instance = self.model_class(**attrs)
        self.session.add(instance)
        return instance

    def update(self, instance, attrs: dict):
        for key, value in attrs.items():
            setattr(instance, key, value)
        return instance

    def delete(self, instance):
        self.session.delete(instance)

    def commit(self):
        self.session.commit()
