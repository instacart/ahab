====
Ahab
====

.. image:: ahab.png

It's easy to install Ahab:

.. code:: bash

    pip install ahab

To get detailed information about Docker events from the command line:

.. code:: bash

    ahab --console debug

To use Ahab as library, you can pass functions to the ``Ahab()`` constructor:

.. code:: python

    def f(event, data):
        pass        # Handle the Docker event (and extended info, as available)


    ahab = Ahab(handlers=[f])
    ahab.listen()

Or subclass ``Ahab``:

.. code:: python

    class Queequeg(Ahab):
        def handle(self, event, data):
            pass                                               # Your code here
