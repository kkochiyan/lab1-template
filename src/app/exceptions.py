class PersonNotFoundError(Exception):
    def __init__(self, person_id: int):
        self.person_id = person_id
        super().__init__(f"Person with id {person_id} was not found")
