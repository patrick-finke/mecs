from mecs import Scene, CommandBuffer

def maplink(scene, source, direction, destination):
    """Link a source location to a destination location via a direction."""

    reversemap = {"north": "south", "south": "north",
                  "west": "east", "east": "west",
                  "northeast": "southwest", "southwest": "northeast",
                  "southeast": "northwest", "northwest": "southeast",
                  "up": "down", "down": "up"}

    assert direction in reversemap, "unknown direction"
    assert scene.has(source, Map), "the source room is missing a Map component"
    assert scene.has(destination, Map), "the destination room is missing a Map component"

    scene.get(source, Map)[direction] = destination
    scene.get(destination, Map)[reversemap[direction]] = source

def move(scene, entity, container):
    """Move an entity from its location container to another container."""

    assert scene.has(container, Container), "the container is missing a Container component"

    if scene.has(entity, Location):
        location = scene.get(entity, Location)
        assert scene.has(location, Container), "the location of the entity is missing a Container component"

        scene.get(location, Container).remove(entity)

    scene.set(entity, Location(container))
    scene.get(container, Container).append(entity)

def listjoin(lst, connector="and"):
    """List things like in a sentence."""

    lst = list(lst)
    if not lst: return ""
    if len(lst) == 1: return lst[0]
    return f"{', '.join(lst[:-1])} {connector} {lst[-1]}"

def findByName(scene, name, container):
    """Return the first entity id that has a matching name component."""

    return next(iter(eid for eid in container if scene.has(eid, Name) and scene.get(eid, Name).match(name)), None)

class Player():
    """Tag for the player entity."""

    pass

class Name():
    def __init__(self, name, article=None):
        self.name, self.article = name, article

    def get(self, definite=False):
        article = ""
        if self.article:
            article = "the " if definite else f"{self.article} "
        return f"{article}{self.name}"

    def match(self, string):
        return string.lower() == self.name.lower()

class Description(str):
    """Description that can be seen when looking at/examining things."""
    pass

class Inscription(str):
    """An inscription that can be read."""
    pass

class Location(int):
    """An entity that can be moved into different container entities."""
    pass

class Container(list):
    """An entity that can contain other enitites."""
    pass

class Map(dict):
    """Map directions to locations."""
    pass

class Environment(str):
    """Mark an entity as belonging to the environment with an optional message
    that will be displayed alongside the destcription of the location.
    """
    pass

class CommandSystem():
    """Processes player commands."""

    def __init__(self):
        # a list of all commands and the corresponding methods
        self._COMMANDS = {
            "help": self.cmdHelp,
            "look": self.cmdLook, "l": self.cmdLook,
            "examine": self.cmdExamine, "x": self.cmdExamine,
            "go": self.cmdGo,
            "north": self.cmdNorth, "n": self.cmdNorth,
            "south": self.cmdSouth, "s": self.cmdSouth,
            "west": self.cmdWest, "w": self.cmdWest,
            "east": self.cmdEast, "e": self.cmdEast,
            "northwest": self.cmdNorthwest, "nw": self.cmdNorthwest,
            "northeast": self.cmdNortheast, "ne": self.cmdNortheast,
            "southwest": self.cmdSouthwest, "sw": self.cmdSouthwest,
            "southeast": self.cmdSoutheast, "se": self.cmdSoutheast,
            "up": self.cmdUp, "u": self.cmdUp,
            "down": self.cmdDown, "d": self.cmdDown,
            "inventory": self.cmdInventory, "i": self.cmdInventory,
            "take": self.cmdTake,
            "drop": self.cmdDrop,
            "read": self.cmdRead
        }

        # documentation for each command
        self._HELP = {
            "help": "Get help for a specific command with 'help <command>'.",
            "look": "You can look at your environment with 'look' or at specific things with 'look <thing>'. The shorthand for 'look' is 'l'.",
            "examine": "You can examine things with 'examine <thing>'. This is the same as 'look <thing>'. The shorthand for 'examine' is 'x'.",
            "go": "You can move through the world with 'go <direction>' where north, south, west, east, northwest, northeast, southwest, southeast, up, and down are valid directions. Their shorthands are n, s, w, e, nw, ne, sw, se, u, and d. You can also use the direction directly, without writing 'go' explicitly. For instance to go north use 'go north' or 'north' or 'n'.",
            "inventory": "You can view the things that you are carrying with this command. The shorthand is 'i'.",
            "take": "To add something to your inventory use 'take <thing>'. To take something from a container use 'take <thing> from <container>'.",
            "drop": "Drop things in your inventory with 'drop <thing>'. To drop something into a container use 'drop <thing> into <container>'.",
            "read": "You can read a book or some other text with 'read <thing>'."
        }

    def cmdHelp(self, scene, player, *args):
        """Get help for other commands.

        help            get a list of commands
        help <command>  view the documentation for a specific command
        """

        if len(args) == 1:
            cmd, = args

            if cmd not in self._HELP:
                return "There is no such command. Try 'help' for a list or commands."

            return self._HELP[cmd]
        else:
            msg = "Get further help with 'help <command>'."
            msg += "\nThe following commands are available:"

            for cmd in self._HELP:
                msg += f"\n  {cmd}"

            return msg

    def cmdLook(self, scene, player, *args):
        """Look at the world or things.

        look          view a description of your location
        look <thing>  view the description of a thing at your location or in your inventory
        """

        assert scene.has(player, Location, Container), "The player is lacking vital components."
        location = scene.get(player, Location)

        if len(args) == 0:
            assert scene.has(location, Name, Description, Container, Map), "The players location is lacking vital components"

            things = [eid for eid in scene.get(location, Container) if eid != player and scene.has(eid, Name) and not scene.has(eid, Environment)]
            env = [scene.get(eid, Environment) for eid in scene.get(location, Container) if scene.has(eid, Environment) and scene.get(eid, Environment)]

            msg = f"{scene.get(location, Name).get()}\n\n"
            msg += f"{scene.get(location, Description)}"
            if env:
                msg += " " + " ".join(env)
            msg += "\n\n"
            if things:
                displaynames = []
                for thing in things:
                    name = scene.get(thing, Name).get(definite=False)
                    displaynames.append(name)
                msg += f"Here {'are' if len(displaynames) > 1 else 'is'} {listjoin(displaynames, connector='and')}.\n\n"
            msg += f"You can go {listjoin(scene.get(location, Map).keys(), connector='or')}."
            return msg
        else:
            name = " ".join(args)
            thing = findByName(scene, name, scene.get(location, Container) + scene.get(player, Container))
            if thing is None:
                return "There is no such thing."

            if not scene.has(thing, Description) and not scene.has(thing, Container):
                return f"There is nothing special about {scene.get(thing, Name).get(definite=True)}."

            msg = ""
            if scene.has(thing, Description):
                msg += f"{scene.get(thing, Description)}"
            if scene.has(thing, Container):
                things = [scene.get(eid, Name).get(definite=False) for eid in scene.get(thing, Container) if scene.has(eid, Name)]
                if things:
                    msg += f" It contains " + listjoin(things, connector="and") + "."
                else:
                    msg += f" It is empty."
            return msg

    def cmdExamine(self, scene, player, *args):
        """Examine things.

        examine <thing>  equivalent to 'look <thing>'
        """

        if not args:
            return "You have to name a thing to examine."

        return self.cmdLook(scene, player, *args)

    def cmdGo(self, scene, player, *args):
        """Traverse the world.

        go <direction>  move in the direction
        <direction>     equivalent to 'go <direction>'
        """

        if not args:
            return "You have to name a direction to go towards."

        assert scene.has(player, Location), "The player is lacking vital components."
        location = scene.get(player, Location)
        assert scene.has(location, Map), "The players location is lacking vital components."
        map = scene.get(location, Map)

        direction = " ".join(args)

        expansion = {"n": "north", "s": "south", "w": "west", "e": "east",
                     "nw": "northwest", "ne": "northeast", "sw": "southwest", "se": "southeast",
                     "u": "up", "d": "down"}
        if direction in expansion.keys():
            direction = expansion[direction]

        if direction not in map:
            return "You cannot go this way."

        destination = map[direction]
        move(scene, player, destination)

        return self.cmdLook(scene, player)

    # BEGIN: shorthands for 'go'
    def cmdNorth(self, scene, player, *args):
        return self.cmdGo(scene, player, "north", *args)

    def cmdSouth(self, scene, player, *args):
        return self.cmdGo(scene, player, "south", *args)

    def cmdEast(self, scene, player, *args):
        return self.cmdGo(scene, player, "east", *args)

    def cmdWest(self, scene, player, *args):
        return self.cmdGo(scene, player, "west", *args)

    def cmdNorthwest(self, scene, player, *args):
        return self.cmdGo(scene, player, "northwest", *args)

    def cmdSouthwest(self, scene, player, *args):
        return self.cmdGo(scene, player, "southwest", *args)

    def cmdNortheast(self, scene, player, *args):
        return self.cmdGo(scene, player, "northeast", *args)

    def cmdSoutheast(self, scene, player, *args):
        return self.cmdGo(scene, player, "southeast", *args)

    def cmdUp(self, scene, player, *args):
        return self.cmdGo(scene, player, "up", *args)

    def cmdDown(self, scene, player, *args):
        return self.cmdGo(scene, player, "down", *args)
    # END: shorthands for 'go'

    def cmdInventory(self, scene, player, *args):
        """View your inventory.

        inventory  list the things your are carrying.
        """

        assert scene.has(player, Container), "The player is lacking a vital component."
        inventory = scene.get(player, Container)

        names = [scene.get(eid, Name).get(definite=False) for eid in inventory if scene.has(eid, Name)]
        if not names:
            return "You are carrying nothing."

        msg = "You carry the following things:"
        for name in names:
            msg += f"\n  {name}"

        return msg

    def cmdTake(self, scene, player, *args):
        """Add something to your inventory.

        take <thing>                   take a thing that is at the same location as your are.
        take <thing> from <container>  take a thing from a container that is at the same location as your or in your inventory.
        """
        if not args:
            return "You have to name a thing to take."

        assert scene.has(player, Location, Container), "The player is lacking vital components"
        location = scene.get(player, Location)
        assert scene.has(location, Container), "The players location is lacking a vital component"

        name = " ".join(args)
        container = scene.get(location, Container) + scene.get(player, Container)
        if " from " in name:
            name, containername = name.split(" from ")
            container = findByName(scene, containername, container)
            if container is None:
                return "There is no such container."
            if not scene.has(container, Container):
                return "You cannot do that."
            container = scene.get(container, Container)
        thing = findByName(scene, name, container)
        if thing is None:
            return "There is no such thing."

        if scene.has(thing, Location) and scene.get(thing, Location) == player:
            return "You already have that."

        if scene.has(thing, Environment):
            return "You are unable to take that."

        move(scene, thing, player)

        return "Taken."

    def cmdDrop(self, scene, player, *args):
        """Remove things from your inventory.

        drop <thing>                   drop something from your inventory to your location
        drop <thing> into <container>  drop something from your inventory into a container
        """

        if not args:
            return "You have to name a thing to drop."

        assert scene.has(player, Location, Container), "The player is lacking vital components"
        location = scene.get(player, Location)
        assert scene.has(location, Container)

        name = " ".join(args)
        if " into " in name:
            name, containername = name.split(" into ")
            container = findByName(scene, containername, scene.get(player, Container) + scene.get(location, Container))
            if container is None:
                return "There is no such container."
            if not scene.has(container, Container):
                return "You cannot do that."
        else:
            container = location
        thing = findByName(scene, name, scene.get(player, Container) + scene.get(location, Container))
        if thing is None:
            return "There is no such thing."

        assert scene.has(thing, Location), "The thing is missing a vital component"
        if scene.get(thing, Location) != player:
            return "You do not have that."

        if thing == container:
            return "You cannot do that."

        move(scene, thing, container)

        return "Dropped."

    def cmdRead(self, scene, player, *args):
        """Read something.

        read <thing>  read something (like a book).
        """

        if not args:
            return "You have to name a thing you want to read."

        assert scene.has(player, Container, Location), "The player is lacking vital components"
        location = scene.get(player, Location)
        assert scene.has(location, Container)

        name = " ".join(args)
        thing = findByName(scene, name, scene.get(player, Container) + scene.get(location, Container))
        if thing is None:
            return "There is no such thing."

        if not scene.has(thing, Inscription):
            return "There is nothing to read."

        return f"It says: '{scene.get(thing, Inscription)}'"

    def onStart(self, scene, **kwargs):
        """Execute the 'look' command on start."""

        for eid, (player,) in scene.select(Player):
            print(self._COMMANDS["look"](scene, eid))

    def onUpdate(self, scene, **kwargs):
        """Ask for player input and execute commands."""

        for eid, (player,) in scene.select(Player):
            cmd, *args = input("> ").lower().split()
            print()

            if cmd in self._COMMANDS:
                print(self._COMMANDS[cmd](scene, eid, *args))
            else:
                print("You don't know how to do this, but you can always ask for 'help'.")

def main():
    # set up the scene
    scene = Scene()

    livingroom = scene.new(
        Name("The Living Room"),
        Description("This is the living room."),
        Container((
            scene.new(
                Name("plant", article="a"),
                Description("It has seen better days."),
                Environment("Over in the corner there is a plant.")
            ),
            scene.new(
                Name("picture", article="a"),
                Description("A boat on a lake."),
                Environment("There is a picture on the wall.")
            ),
            scene.new(
                Name("window", article="a"),
                Description("The sun is shining outside."),
                Environment("On the west side of the room there is a window.")
            ),
            scene.new(
                Name("rug", article="a"),
                Description("An antique oriental rug."),
                Environment("There is a rug on the floor.")
            )
        )),
        Map()
    )

    garden = scene.new(
        Name("The Garden"),
        Description("This is the garden."),
        Container((
            scene.new(
                Name("tree"),
                Description("It's an apple tree."),
                Environment("In the middle of the garden is a large tree.")
            ),
        )),
        Map()
    )

    maplink(scene, livingroom, "west", garden)

    player = scene.new(
        Player(),
        Name("Player"),
        Description("This is you."),
        Container(),
    )
    move(scene, player, livingroom)

    book = scene.new(
        Name("book", article="a"),
        Description("'Alice's Adventures in Wonderland' by Lewis Carroll."),
        Inscription("Alice was beginning to get very tired of sitting by her sister on the bank, and of having nothing to do: once or twice she had peeped into the book her sister was reading, but it had no pictures or conversations in it, 'and what is the use of a book,' thought Alice 'without pictures or conversations?'")
    )
    move(scene, book, livingroom)

    box = scene.new(
        Name("box", article="a"),
        Description("A box."),
        Container()
    )
    move(scene, box, livingroom)

    dice = scene.new(
        Name("die", article="a"),
        Description("A small die.")
    )
    move(scene, dice, box)

    marble = scene.new(
        Name("marble", article="a"),
        Description("A white marble.")
    )
    move(scene, marble, livingroom)

    shovel = scene.new(
        Name("shovel", article="a"),
        Description("A small chrome shovel.")
    )
    move(scene, shovel, garden)

    # sort systems
    systems = [CommandSystem()]
    startSystems = [s for s in systems if hasattr(s, 'onStart')]
    updateSystems = [s for s in systems if hasattr(s, 'onUpdate')]

    # main loop
    try:
        scene.start(*startSystems)
        while True: scene.update(*updateSystems)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
