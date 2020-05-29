# mecs

**`mecs` is an implementation of the Entity Component System (ECS) paradigm for Python 3, with a focus on interface minimalism and performance.**

Inspired by [Esper](https://github.com/benmoran56/esper) and Sean Fisk's [ecs](https://github.com/seanfisk/ecs).

### Contents
 - [Changelog](#changelog)
 - [Installation](#installation)
 - [About the ECS paradigm](#ecs-paradigm)
 - [Using `mecs` in your project](#mecs-usage)
    - [Managing entities](#mecs-entities)
    - [Implementing and managing components](#mecs-componentes)
    - [Implementing and running systems](#mecs-systems)
 - [Recipes](#recipes)

<a name="changelog"/>

## Changelog

For a full list of changes see [CHANGELOG.md](CHANGELOG.md).

- **v1.2.0 - Add support for manipulating multiple components at once**

  The methods `scene.new()`, `scene.set()`, `scene.has()`, and `scene.remove()` (where `set()` replaces `add()`) now support multiple components/component types. The appropriate methods have also been modified in the `CommandBuffer`. `scene.get()` now has a conterpart `scene.collect()` which supports multiple component types. Minor changes include better exception messages and `scene.buffer()` being deprecated in favour of `CommandBuffer(scene)`.

- **v1.1.0 - Add command buffer**

  When using `scene.select()`, manipulation of entities can now be recorded using the `CommandBuffer` instance returned by `scene.buffer()`, and played back at a later time. This avoids unexpected behavior that would occur when using the scene instance directly.

- **v1.0.0 - First release**

  The base functionality is implemented. Note that at this stage it is not safe to add or remove components while iterating over their entities. This will be fixed in a future release.

<a name="installation"/>

## Installation

`mecs` is implemented in a single file with no dependencies. Simply copy `mecs.py` to your project folder and `import mecs`.

<a name="ecs-paradigm"/>

## About the ECS paradigm

The Entity Component System (ECS) paradigm consists of three different concepts, namely **entities**, **components** and **systems**. These should be understood as follows:

1. **Entities** are unique identifiers, labeling a set of components as belonging to a group.
2. **Components** are plain data and implement no logic. They define the behavior of entities.
3. **Systems** are logic that operates on entities and their component, enforcing the appropriate behavior of entities with certain component types. Moreover, they are able to add and remove components from entities or mutate the data of existing components, effectively changing the entities behavior.

For more information about the ECS paradigm, visit the [Wikipedia article](https://en.wikipedia.org/wiki/Entity_component_system) or Sander Mertens' [ecs-faq](https://github.com/SanderMertens/ecs-faq).

<a name="mecs-usage"/>

## Using `mecs` in your project
For the management of entities, components and systems, `mecs` provides the `Scene` class. Only entities within the same scene may interact with one another. You can create a new scene with

```python
scene = Scene()
```

<a name="mecs-entities"/>

### Managing entities

Entities are nothing more than unique (integer) identifiers. To get hold of a previously unused **entity id** use

```python
eid = scene.new()
```

Note that there is no method to remove or invalidate an entity id. There are no drawbacks to this decision, as entities that do not have components consume no memory and there is no way practical way of running out of entity ids. Furthermore, it alleviates the problem where a reference to an entity id does point to a nonsensical entity, because the originally referenced entity was destroyed and the entity id was then reused.

<a name="mecs-componentes"/>

### Implementing and managing components

Components can be instances of any class and `mecs` does not provide a base class for them. For example a `Position` component containing `x` and `y` coordinates could look like this:

```python
class Position():
  def __init__(self, x, y):
    self.x, self.y = x, y
```

Other examples would be a similar `Velocity` component or a `Renderable` component:

```python
class Velocity():
  def __init__(self, vx, vy):
    self.vx, self.vy = vx, vy

class Renderable():
  def __init__(self, textureId):
    self.textureId = textureId
```

Components are distinguished by their **component type**. It is important to note that entities can only contain up to one component of each type. While this allows for better performance when retrieving components, it may seem restrictive in some cases. If you are absolutely sure you need more than one component of a type attached to one entity, take a look at the [recipes](#recipes). To get the type of a component use the build-in `type()`:

```python
position = Position(15, 8)
type(position)
# => <class '__main__.Position'>

velocity = Velocity(8, 15)
type(velocity)
# => <class '__main__.Velocity'>
```

\
\
The `Scene` class provides the following methods for interacting with entities and components. Note that the entity id used in these methods must be valid, i.e. must be returned from `scene.new()`. Using an invalid entity id results in a `KeyError`.

#### 1. Setting components while allocating a new entity id using `scene.new(*comps)`.

Returns a valid entity id to be used in other methods. It is also possible to directly set components of the new entity by supplying them to this method.

```python
 # create a new empty entity
eid = scene.new()
# => 0

# create a new entity with a Position, Velocity and Renderable component
anotherEid = scene.new(Position(15, 8), Velocity(8, 15), Renderable(7))
# => 1
```

Raises `ValueError` if trying to set one or more components of the same type.

#### 2. Setting components using `scene.set(eid, *comps)`.

Set components of an entity, which can either result in adding a component or overwriting an existing component. Note that an entity is only allowed to have one component of each type.

```python
# Add a new Position component
scene.set(eid, Position(1, 2))

# Overwrite the Position component
scene.set(eid, Position(3, 4))

# Add a Velocity component and overwrite the Position component again
scene.set(eid, Velocity(0, -5), Position(5, 6))
```

Setting components of the same type in a single call to `set()` is illegal and results in a `ValueError`. Note that the same component instance can be added to multiple entities, making them share the component data.

#### 3. Check if components are part of an entity using `scene.has(eid, *comptypes)`.

This method returns `True` if the entity does have components of all the specified types, `False` otherwise.

```python
# check for Position component (the entity has one)
scene.has(eid, Position)
# => True

# check for Position and Velocity (the entity has both)
scene.has(eid, Position, Velocity)
# => True

# check for Position and Renderable (the entity has a Position but is lacking the Renderable component)
scene.has(eid, Position, Renderable)
# => False
```

Raises `ValueError` is no component type is supplied to the method.

#### 4. Getting single components using `scene.get(eid, comptype)`.

Returns the component of the specified type, allowing to view or edit the component data.

```python
# move the entity by 10 units on the x-axis
position = scene.get(eid, Position)
position.x += 10

# stop the entity by setting its velocity to zero
velocity = scene.get(eid, Velocity)
velocity.vx, velocity.vy = 0, 0
```

Raises `ValueError` if the entity does not have a component of the requested type.

#### 5. Getting multiple components at once using `scene.collect(eid, *comptypes)`.

Returns a list of the entities components of the specified types.

```python
# repeat the example from above
position, velocity = scene.collect(eid, Position, Velocity)
position.x += 10
velocity.vx, velocity.vy = 0, 0
```

Raises `ValueError` if the entity is missing one or more components of the requested types.

#### 6. Removing components using `scene.remove(eid, *comptype)`.

Removes the components of the specified types from the entity.

```python
# remove the Position and the Velocity component
scene.remove(eid, Position, Velocity)
```

Raises `ValueError` if the entity is missing one or more components of the specified types.

#### 7. Removing all components from an entity using `scene.free(eid)`.

Removes all components of the entity.

```python
scene.set(eid, Position(0, 0), Velocity(0, 0))

scene.free(eid)

scene.has(eid, Position) or scene.has(eid, Velocity) or scene.has(eid, Renderable)
# => False
```

Note that this does not make the entity id invalid. In fact, there is no way to invalidate a once valid id. In particular, there is no method to check if an entity is still 'alive'. If you need such behavior, take a look at the [recipes](#recipes).

#### 8. Viewing the archetype of an entity and all of its components using `scene.archetype(eid)` and `scene.components(eid)`.

The **archetype** of an entity is the tuple of all component types that are attached to it.

```python
scene.set(eid, Position(32, 64), Velocity(8, 16))

scene.archetype(eid)
# => (<class '__main__.Position'>, <class '__main__.Velocity'>)

scene.components(eid)
# => (<__main__.Position object at 0x000001EF0358D370>, <__main__.Velocity object at 0x000001EF035B47C0>)
```

The result of `scene.archetype(eid)` is sorted, so comparisons of the form `scene.archetype(eid1) == scene.archetype(eid2)` are possible, but hardly necessary.

#### 9. Iterating over entities and components using `scene.select(*comptypes, exclude=None)`.

The result of this method is a generator object yielding tuples of the form `(eid, (compA, compB, ...))` where `compA`, `compB` belong to the entity with entity id `eid` and have the requested types. Optionally, an iterable (such as a list or tuple) may be passed to the `exclude` argument, in which case all entities having one or more component types listed in `exclude` will not be yielded by the method.

```python
# adjust positions based on velocity
dt = current_deltatime()
for eid, (pos, vel) in scene.select(Position, Velocity):
  pos.x += vel.vx * dt
  pos.y += vel.vy * dt
```

Iterating over entities that have a certain set of components is one of the most important tasks in the ECS paradigm. Usually, this is done by systems to efficiently apply their logic to the appropriate entities. For more examples, see the section about [systems](#mecs-systems).

#### 10. Staying save using the `CommandBuffer`.

Methods such as `scene.new()`, `scene.set()`, `scene.remove()`, or `scene.free()` alter the structure of the underlying database of the scene. This makes them *not save* to use while iterating over the result of `scene.select()`. Using them in this context *will not* raise any exceptions, but will often lead to unexpected behaviour.

To resolve this issue, `mecs` provides the `CommandBuffer` class, which implements `CommandBuffer.new(*comps)`, `CommandBuffer.set(eid, *comps)`, `CommandBuffer.remove(eid, *comptypes)`, and `CommandBuffer.free(eid)`. Any calls to these methods will be recorded, and when it is save to do so, can be played back using `CommandBuffer.flush()`. Alternatively, the command buffer can be used as a context manager, which is strongly recommended.

```python
# remove all entities from the scene that are not withing the screen bounds
with CommandBuffer(scene) as buffer:
  for eid, (pos,) in scene.select(Position):
   if pos.x < 0 or pos.x > screen_width or pos.y < 0 or pos.y > screen_height:
     buffer.free(eid)
```

<a name="mecs-systems"/>

### Implementing and running systems

As with components, `mecs` does not provide a base class for systems. Instead, a system should implement any of the three callback methods (`onStart()`, `onUpdate()`, and `onStop()`) and must be passed to the corresponding method of the `Scene` class.

#### 1. Initializing a scene using `scene.start(*systems, **kwargs)`.

Any instance of any class that implements a method with the signature `onStart(scene, **kwargs)` may be used as an input to this method.

The scene iterates through all systems in the order they are passed and calls their respective `onStart()` methods, passing itself using the `scene` argument. Additionally, any `kwargs` will also be passed on.

```python
class RenderSystem():
  def onStart(self, scene, resolution=(600, 480), **kwargs):
    self.graphics = init_graphics_devices(resolution)
    self.textures = load_textures("./resources/textures")

renderSystem = RenderSystem()
startSystems = [renderSystem, AnotherInitSystem()]
scene.start(*startSystems, resolution=(1280, 720))
```

This method should *not* be called multiple times. Instead, all necessary systems should be instantiated first, followed by a single call to `scene.start()`.

#### 2. Updating a scene using `scene.update(*systems, **kwargs)`.

Any instance of any class that implements a method with the signature `onUpdate(scene, **kwargs)` may be used as an input to this method.

The scene iterates through all systems in the order they are passed and calls their respective `onUpdate()` methods, passing itself using the `scene` argument. Additionally, any `kwargs` will also be passed on.

```python
class RenderSystem():
  def onUpdate(self, scene, **kwargs):
    for eid, (pos, rend) in scene.select(Position, Renderable):
      texture = self.textures[rend.textureId]
      self.graphics.render(pos.x, pos.y, texture))

class MovementSystem():
  def onUpdate(self, scene, dt=1, **kwargs):
    for eid, (pos, vel) in scene.select(Position, Velocity):
      pos.x += vel.vx * dt
      pos.y += vel.vy * dt

updateSystems = [MovementSystem(), renderSystem]
scene.update(*updateSystems, dt=current_deltatime())
```

To avoid any unnecessary overhead, call this method only once per update circle, passing all necessary systems as arguments.

#### 3. Cleaning up a scene using `scene.stop(*systems, **kwargs)`.

Any instance of any class that implements a method with the signature `onStop(scene, **kwargs)` may be used as an input to this method.

The scene iterates through all systems in the order they are passed and calls their respective `onStop()` methods, passing itself using the `scene` argument. Additionally, any `kwargs` will also be passed on.

```python
class RenderSystem():
  def onStop(self, scene, **kwargs):
    stop_graphics_devices(self.graphics)
    unload_textures(self.textures)

stopSystems = [renderSystem, AnotherDestroySystem()]
scene.stop(*stopSystems)
```

As with `scene.start()` this method should *not* be called multiple times, but instead once with all the necessary systems.

<a name="recipes"/>

### Useful patterns

This section collects common patterns that may be useful when using `mecs`.

#### Update loop

A basic update loop. The scene will be started, continuously updated and safely stopped (with Ctrl+C), using the appropriate systems.

```python
# Your system instances go here.
systems = []

startSystems = [s for s in systems if hasattr(s, 'onStart')]
updateSystems = [s for s in systems if hasattr(s, 'onUpdate')]
stopSystems = [s for s in systems if hasattr(s, 'onStop')]

print("[Press Ctrl+C to stop]")
try:
  scene = Scene()
  scene.start(*startSystems)
  while True:
    deltaTime = current_deltatime()
    scene.update(*updateSystems, dt=deltaTime)
except KeyboardInterrupt:
  pass
finally:
  scene.stop(*stopSystems)
```

#### Check if an entity is alive

In `mecs` there is no concept of 'alive' for an entity. An entity id can either be valid (in which case its components may be manipulated) or invalid (where attempted component manipulation results in an exception). A once valid entity id cannot be invalidated. To check if an entity is alive, consider tagging it with an `Alive` component when creating it and then checking for that component.

```python
class Alive():
  """Every entity that is alive has one of these."""

# create an entity that is alive
scene = Scene()
eid = scene.new(Alive())

# Is the entity alive?
scene.has(eid, Alive)
# => True

# 'destroy' the entity
scene.free(eid)

# Is the entity alive?
scene.has(eid, Alive)
# => False
```

#### Add multiple components of the same type

Often, adding multiple components of the same type can be avoided by carefully designing components and systems. If it is necessary, consider implementing a component that itself is a collection of components.

```python
class Dead():
  """Every entity with this component is marked as dead."""
  pass

class Health():
  """The health value of an entity. If this is zero the entity should die."""
  def __init__(self, value):
    self.value = value

class DamageStack(list):
  """A list of damage components."""

class Damage():
  """Damage that should be dealt to an entity."""
  def __init__(self, amount):
    self.amount = amount

# setup an entity
scene = Scene()
eid = scene.new(Health(100))

# apply damage to the entity
if not scene.has(eid, DamageStack):
  scene.set(eid, DamageStack())
scene.get(eid, DamageStack).append(Damage(10))

# resolve the damage
class ResolveDamageSystem():
  def onUpdate(self, scene, **kwargs):
    with CommandBuffer(scene) as buffer:
      for eid, (health, damage) in scene.select(Health, DamageStack):
        # apply all the damage
        health.value -= sum(dmg.amount for dmg in damage)

        # if the entity has no health left, set the death flag
        if health.value <= 0:
          health.value = 0
          buffer.add(eid, Dead())

        # the damage stack has been processed, remove it
        buffer.remove(eid, DamageStack)
```
