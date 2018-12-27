"""
synthetic.py provides functions to add synthetic values to a model grid.

Values can be added to any valid grid element (e.g. link or node). If no field
exists, a field of float zeros will be initialized.

All functions add values to the field---this means that multiple functions can
be chained together.

All functions support adding values to only portions of the grid, based on the
``status_at_link`` and ``status_at_node`` attributes.

For example, if one wanted to construct an initial topographic elevation
represented by a tetrahedron and add normally distributed noise only to core
nodes, this could be acomplished as follows:

Examples
--------
>>> import numpy as np
>>> from landlab import RasterModelGrid
>>> from landlab import CORE_NODE
>>> from landlab.values import random, plane
>>> np.random.seed(42)

Create the grid.

>>> mg = RasterModelGrid((7, 7))

Create a tetrahedron by adding planes selectively using ``where``.

>>> southwest = plane(mg, 'topographic__elevation',
...                   where=((mg.x_of_node <= 3) & (mg.y_of_node <= 3)),
...                   point=(0, 0, 0), normal=(-1, -1, 1))
>>> southeast = plane(mg, 'topographic__elevation',
...                   where=((mg.x_of_node > 3) & (mg.y_of_node <= 3)),
...                   point=(6, 0, 0), normal=(1, -1, 1))
>>> northeast = plane(mg, 'topographic__elevation',
...                   where=((mg.x_of_node > 3) & (mg.y_of_node > 3)),
...                   point=(6, 6, 0), normal=(1, 1, 1))
>>> northwest = plane(mg, 'topographic__elevation',
...                   where=((mg.x_of_node <= 3) & (mg.y_of_node > 3)),
...                   point=(0, 6, 0), normal=(-1, 1, 1))
>>> mg.at_node['topographic__elevation']
array([ 0.,  1.,  2.,  3.,  2.,  1.,  0.,
        1.,  2.,  3.,  4.,  3.,  2.,  1.,
        2.,  3.,  4.,  5.,  4.,  3.,  2.,
        3.,  4.,  5.,  6.,  5.,  4.,  3.,
        2.,  3.,  4.,  5.,  4.,  3.,  2.,
        1.,  2.,  3.,  4., 3.,   2.,  1.,
        0.,  1.,  2.,  3.,  2.,  1.,  0.])

Next add uniformly distributed noise.

>>> noise = random(mg, 'topographic__elevation',
...                where=CORE_NODE,
...                distribution='uniform')
>>> np.round(mg.at_node['topographic__elevation'], decimals=3)
array([ 0.   ,  1.   ,  2.   ,  3.   ,  2.   ,  1.   ,  0.   ,
        1.   ,  2.375,  3.951,  4.732,  3.599,  2.156,  1.   ,
        2.   ,  3.156,  4.058,  5.866,  4.601,  3.708,  2.   ,
        3.   ,  4.021,  5.97 ,  6.832,  5.212,  4.182,  3.   ,
        2.   ,  3.183,  4.304,  5.525,  4.432,  3.291,  2.   ,
        1.   ,  2.612,  3.139,  4.292,  3.366,  2.456,  1.   ,
        0.   ,  1.   ,  2.   ,  3.   ,  2.   ,  1.   ,  0.   ])

At present only a small selection of possible synthetic functions exist. If
your research requires additional functions, consider contributing one back to
the main landlab repository. If you have questions on how to proceed, please
create a GitHub issue.

All public functions from this submodule should have a common format. They
take as the first two arguments a model grid, and the name of the field.
They all take two keyword arguments: ``at``, which specifies which grid element
values are placed, and ``where``, which indicates where the values are placed.
Additional keyword arguments are required as needed by each function.
"""
import numpy as np

from landlab import NetworkModelGrid


def _create_missing_field(grid, name, at):
    """Create field of zeros if missing."""
    if name not in grid[at]:
        grid.add_zeros(at, name)


def _where_to_add_values(grid, at, where):
    "Determine where to put values."
    where_to_place = np.zeros(grid.size(at), dtype=bool)

    try:
        where.size == grid.size(at)
        where_to_place = where
    except AttributeError:

        if at is "link":
            status_values = grid.status_at_link
        elif at is "node":
            status_values = grid.status_at_node
        else:
            if where is not None:
                raise ValueError(
                    (
                        "No status information exists for grid "
                        "elements that are not nodes or links."
                    )
                )
        # based on status, set where to true. support value or iterable.
        if where is None:
            where_to_place = np.ones(grid.size(at), dtype=bool)
        else:
            try:
                for w in where:
                    where_to_place[status_values == w] = True
            except TypeError:
                where_to_place[status_values == where] = True

    return where_to_place


def random(grid, name, at="node", where=None, distribution="uniform", **kwargs):
    """Add random values to a grid.

    This function supports all distributions provided in the
    `numpy.random submodule
    <https://docs.scipy.org/doc/numpy-1.15.1/reference/routines.random.html#distributions>`_.

    Parameters
    ----------
    grid : ModelGrid
    name : str
        Name of the field.
    at : str, optional
        Grid location to store values. If not given, values are
        assumed to be on `node`.
    where : optional
        The keyword ``where`` indicates where synthetic values
        should be placed. It is either (1) a single value or list
        of values indicating a grid-element status (e.g. CORE_NODE),
        or (2) a (number-of-grid-element,) sized boolean array.
    distribution : str, optional
        Name of the distribution provided by the np.random
        submodule.
    kwargs : dict
        Keyword arguments to pass to the ``np.random`` distribution
        function.

    Returns
    -------
    values : array
        Array of the values added to the field.

    Examples
    --------
    >>> import numpy as np
    >>> from landlab import RasterModelGrid
    >>> from landlab import CORE_NODE
    >>> from landlab.values import random
    >>> np.random.seed(42)
    >>> mg = RasterModelGrid((4, 4))
    >>> values = random(mg,
    ...                 'soil__depth',
    ...                 'node',
    ...                 where=CORE_NODE,
    ...                 distribution='uniform',
    ...                 high=3.,
    ...                 low=2.)
    >>> mg.at_node['soil__depth']
    array([ 0.        ,  0.        ,  0.        ,  0.        ,
            0.        ,  2.37454012,  2.95071431,  0.        ,
            0.        ,  2.73199394,  2.59865848,  0.        ,
            0.        ,  0.        ,  0.        ,  0.        ])
    """
    where = _where_to_add_values(grid, at, where)
    _create_missing_field(grid, name, at)
    values = np.zeros(grid.size(at))

    if distribution not in np.random.__dict__:
        raise ValueError("")

    function = np.random.__dict__[distribution]
    values[where] += function(size=np.sum(where), **kwargs)
    grid[at][name][:] += values
    return values


def plane(grid, name, at="node", where=None, point=(0., 0., 0), normal=(0., 0., 1.)):
    """Add a single plane defined by a point and a normal to a grid.

    Parameters
    ----------
    grid : ModelGrid
    name : str
        Name of the field.
    at : str, optional
        Grid location to store values. If not given, values are
        assumed to be on `node`.
    where : optional
        The keyword ``where`` indicates where synthetic values
        should be placed. It is either (1) a single value or list
        of values indicating a grid-element status (e.g. CORE_NODE),
        or (2) a (number-of-grid-element,) sized boolean array.
    point : tuple, optional
        A tuple defining a point the plane goes through in the
        format (x, y, z). Default is (0., 0., 0.)
    normal : tuple, optional
        A tuple defining the normal to the plane in the format
        (dx, dy, dz). Must not be verticaly oriented. Default
        is a horizontal plane (0., 0., 1.).

    Returns
    -------
    values : array
        Array of the values added to the field.

    Examples
    --------
    >>> from landlab import RasterModelGrid
    >>> from landlab.values import plane
    >>> mg = RasterModelGrid((4, 4))
    >>> values = plane(mg,
    ...                'soil__depth',
    ...                'node',
    ...                point=(0., 0., 0.),
    ...                normal=(-1., -1., 1.))
    >>> mg.at_node['soil__depth']
    array([ 0.,  1.,  2.,  3.,
            1.,  2.,  3.,  4.,
            2.,  3.,  4.,  5.,
            3.,  4.,  5.,  6.])

    """
    x, y = _get_x_and_y(grid, at)

    where = _where_to_add_values(grid, at, where)
    _create_missing_field(grid, name, at)
    values = _plane_function(x, y, point, normal)
    grid[at][name][where] += values[where]

    return values


def _plane_function(x, y, point, normal):
    """calculate the plane function"""
    if np.isclose(normal[2], 0):
        raise ValueError("")

    constant = point[0] * normal[0] + point[1] * normal[1] + point[2] * normal[2]
    values = (constant - (normal[0] * x) - (normal[1] * y)) / normal[2]

    return values


def _get_x_and_y(grid, at):
    if isinstance(grid, NetworkModelGrid):
        if at is not "node":
            msg = (
                "Synthetic fields based on x and y values at grid elements "
                "(e.g. sine, plane) are supported for NetworkModelGrid "
                "only at node. If you need this at other grid elements, "
                "open a GitHub issue to learn how to contribute this "
                "functionality."
            )
            raise ValueError(msg)
    if at is "node":
        x = grid.x_of_node
        y = grid.y_of_node
    elif at is "link":
        x = grid.x_of_link
        y = grid.y_of_link
    elif at is "cell":
        x = grid.x_of_cell
        y = grid.y_of_cell
    elif at is "face":
        x = grid.x_of_face
        y = grid.y_of_face
    else:
        msg = (
            "landlab.values.synthetic: ",
            "X and Y values are require for the requested synthetic field "
            "but do not exist for the grid-element provided.",
        )
        raise ValueError(msg)
    return x, y


def constant(grid, name, at="node", where=None, constant=0.):
    """Add a constant to a grid.

    Parameters
    ----------
    grid : ModelGrid
    name : str
        Name of the field.
    at : str, optional
        Grid location to store values. If not given, values are
        assumed to be on `node`.
    where : optional
        The keyword ``where`` indicates where synthetic values
        should be placed. It is either (1) a single value or list
        of values indicating a grid-element status (e.g. CORE_NODE),
        or (2) a (number-of-grid-element,) sized boolean array.
    constant : float, optional
        Constant value to add to the grid. Default is 0.

    Returns
    -------
    values : array
        Array of the values added to the field.

    Examples
    --------
    >>> from landlab import RasterModelGrid
    >>> from landlab import ACTIVE_LINK
    >>> from landlab.values import constant
    >>> mg = RasterModelGrid((4, 4))
    >>> values = constant(mg,
    ...                  'some_flux',
    ...                  'link',
    ...                  where=ACTIVE_LINK,
    ...                  constant=10)
    >>> mg.at_link['some_flux']
    array([  0.,   0.,   0.,   0.,  10.,  10.,   0.,  10.,  10.,  10.,   0.,
            10.,  10.,   0.,  10.,  10.,  10.,   0.,  10.,  10.,   0.,   0.,
             0.,   0.])

    """
    where = _where_to_add_values(grid, at, where)
    _create_missing_field(grid, name, at)
    values = np.zeros(grid.size(at))
    values[where] += constant
    grid[at][name][:] += values
    return values


def sine(
    grid,
    name,
    at="node",
    where=None,
    amplitude=1.,
    wavelength=1.0,
    a=1.0,
    b=1.0,
    point=(0., 0.),
):
    r"""Add a sin wave to a grid.

    Add a sine wave :math:`z` defined as:

    .. math::
        z = A * sin ( \\frac{2\pi v}{\lambda} )
        v = a(x-x_0) + b(y-y_0)

    where :math:`A` is the amplitude and :math:`\lambda` is the wavelength.
    The values :math:`a`, :math:`b`, and the point :math:`(x_0, y_0)` permit
    the sin wave to be oriented arbitrarily in the x-y plane.

    Parameters
    ----------
    grid : ModelGrid
    name : str
        Name of the field.
    at : str, optional
        Grid location to store values. If not given, values are
        assumed to be on `node`.
    where : optional
        The keyword ``where`` indicates where synthetic values
        should be placed. It is either (1) a single value or list
        of values indicating a grid-element status (e.g. CORE_NODE),
        or (2) a (number-of-grid-element,) sized boolean array.
    amplitude : p
    wavelength :
    a :
    b :
    point :

    Returns
    -------
    values : array
        Array of the values added to the field.

    Examples
    --------
    >>> from landlab import RasterModelGrid
    >>> from landlab import ACTIVE_LINK
    >>> from landlab.values import sine
    >>> mg = RasterModelGrid((5, 5))
    >>> values = sine(mg,
    ...               'topographic__elevation',
    ...               amplitude=2, wavelength=4,
    ...               a=1, b=0)
    >>> np.round(mg.at_node['topographic__elevation'], decimals=2)
    array([ 0.,  2.,  0., -2., -0.,
            0.,  2.,  0., -2., -0.,
            0.,  2.,  0., -2., -0.,
            0.,  2.,  0., -2., -0.,
            0.,  2.,  0., -2., -0.])
    """
    x, y = _get_x_and_y(grid, at)

    where = _where_to_add_values(grid, at, where)
    _create_missing_field(grid, name, at)
    values = np.zeros(grid.size(at))
    v = (a * (x - point[0])) + (b * (y - point[1]))
    values[where] += amplitude * np.sin(2. * np.pi * v / wavelength)
    grid[at][name][:] += values
    return values
