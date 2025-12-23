# player.py

# A simple class to hold data about a player.
# We will add more to this later (like position on the set).
class Player:
    def __init__(self, id):
        self.id = id
        self.name = f"Player {id}"

    def __repr__(self):
        return f"Player({self.id}, {self.name})"