Initial Reasons
===============

Why Descriptors
---------------

Pros
~~~~

* More "Pythonic"
* Unsurprising - actual attributes on the class
* (Maybe) Metaclass needs to assign them as normal

    * This might actually make the logic simpler (just dict assignment rather
      than the ``fields`` dict)

Cons
~~~~

* No way to control the behavior without overriding ``__get__`` & co.
* We'd lose the "sorted"-ness of the attributes?

    * Is this even the case? The ``attrs`` dict we get in ``__new__`` might
      already have has randomization or similar. This too needs verification.

* Changing the fields post-init doesn't seem to work right?

    * This needs another test


Why ``__getattr__``
-------------------

Pros
~~~~

* Can stow the fields
* Straight-forward-ish metaclass
* Another hook
* Can keep sort order? (Maybe, see above)
* (Maybe) Easier to extend or change the fields post-init

Cons
~~~~

* Descriptors-based fields no longer (natively) work
* Would require it's own API
* Not as "Pythonic"


Research
========

* Is the sort order of ``attrs`` stable? Can we count on ordering?

    * No, it is **NOT** ordered. Hash randomization is in effect.
    * Neither approach is better here.

* Can we dynamically assign descriptors after an instance is created?

    * Not by simple assignment or ``setattr``.
    * This favors the ``__getattr__``-based approach.

Code used::

    class SimpleField(object):
        name = 'unknown'
        is_field = True

        def __get__(self, obj, type=None):
            if self.name in obj._data:
                return "Hello {0}".format(obj._data[self.name])
            return 'Nope.'


    class TestMeta(type):
        def __new__(cls, name, bases, attrs):
            for name, field in attrs.items():
                print('Saw {0}.'.format(name))

                if getattr(field, 'is_field', False) is True:
                    field.name = name

            return super(TestMeta, cls).__new__(cls, name, bases, attrs)


    class Test(object, metaclass=TestMeta):
        name = SimpleField()
        age = SimpleField()
        data_type = SimpleField()
        request = SimpleField()

        def __init__(self, **kwargs):
            self._data = kwargs


    if __name__ == '__main__':
        test = Test(
            name='Mister',
            age=17,
            data_type='string',
            is_admin=True
        )

        print()
        print("Name is: {0}".format(test.name))
        print("Age is: {0}".format(test.age))
        print("Request is: {0}".format(test.request))

        test.is_admin = SimpleField()
        test.is_admin.name = 'is_admin'

        print("Simple assignment...")
        print("Is Admin is: {0}".format(test.is_admin))

        field = SimpleField()
        field.name = 'is_admin'
        setattr(test, 'is_admin', field)

        print("Setattr assignment...")
        print("Is Admin is: {0}".format(test.is_admin))


Revised Reasons
===============

Why Descriptors
---------------

Pros
~~~~

* More "Pythonic"
* Unsurprising - actual attributes on the class
* (Indeterminate) Metaclass needs to assign them as normal

Cons
~~~~

* No way to control the behavior without overriding ``__get__`` & co.
* Changing the fields post-init isn't easy/obvious


Why ``__getattr__``
-------------------

Pros
~~~~

* Can stow the fields
* Another hook
* Easier to extend or change the fields post-init
* (Indeterminate) Slightly more complex metaclass

Cons
~~~~

* Descriptors-based fields no longer (natively) work
* Would require it's own API
* Not as "Pythonic"


Conclusion
==========

The ``__getattr__``-based approach seems to provide more customizability & hence
more future-proofing. This will be the path boto3 takes.

If the classes were simple or always known up-front, descriptors would win. But
we don't really have that luxury.
