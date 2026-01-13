Standard Transformation and Coordinate System Names
===================================================

In order to maintain interoperability between different software packages standardised
names for some transformations and coordinate systems have been established.

Coordinate Systems
------------------

The starting coordinate systems are named "base_logical_coordinates_2d" and
base_logical_coordinates_3d. Global variables ``BASE_LOGICAL_COORDS_2D`` and
``BASE_LOGICAL_COORDS_3D`` contain these names. Two helper functions are provided in
``cets_data_model.standard_coordinate_systems`` to generate ``CoordinateSystem`` objects.

.. code-block:: python

    logical_coordinates(dim: int, name: Optional[str]=None)
    physical_coordinates(dim: int, name: str)

Each returns the coordinate system with the dimension specified in ``dim`` and correct
name.  If ``logical_coordinates()`` is called without ``name`` it returns the base
coordinates system name for the appropriate dimension.

Standard Alignment Transformations
----------------------------------

There are specific ``CoordinateTransformation`` subclasses for common tasks in the
tomography workflow. This makes it easy to identify the transformation associated with
this processing task by searching for a ``CoordinateTransformation`` of that type in the
CETS data.

Pixel Size
----------

``ImagePixelSize`` and ``ImageSuperResolutionPixelSize`` are subclesses of the ``Scale``
``CoordinateSystemTransform``. They are used to define the physical pixel size for
objects.

Targeted Alignment Transformations
----------------------------------

Targeted transformations are sublasses of the ``Sequence`` ``CoordinateTransformation``
used for aligning an object to another. They have one additional field: the target
object the transformed object is being aligned to

.. csv-table::
    :header: Object aligned, Target, Transformation class, Class type name

    Movie frame, Projection image,``AlignMovieFrame``, align_movie_frame
    Projection image, Tilt series, ``AlignProjectionImage``, align_projection_image
    Subtomogram, Tomogram, ``AlignSubtomogram``, align_subtomogram
    Map, Tomogram, ``AlignMap``, align_map
    Annotation, Tomorgram or image, ``AlignAnnotation``, align_annotation

Examples
--------

You have a projection image entry in your CETS data and want to know the transformations
that aligned it to a tilt series named 'TS1'. Serch the ``coordinate_transformations``
field of the projection for a transformation with ``type`` of ``align_projection_image``
and ``target`` of ``TS1``.

You have a tomogram entry and want to know its physical pixel size. Look in its
``coordinate_transformations`` field for a transformation of ``type`` ``image_pixel_size``.

The ``ImagePixelSize`` for the tomogram

.. code-block:: python

 {
 "type": "image_pixel_size"
 "input": BASE_LOGICAL_COORDS
 "output": "image apix"       # Name this CoordinateSystem can be anything
 "scale": {1.5, 1.5, 1.5}
 }

If you extract binned tomograms from the original tomogram each subtomogram entry will have
``coordinate_transformations`` entry of ``type`` ``image_pixel_size`` which defines the
binned pixel size.

The ``ImagePixelSize`` for the binned subtomograms could take either of these forms, both
are legitimate

.. code-block:: python

  {
    "type": "image_pixel_size"
    "input": BASE_LOGICAL_COORDS
    "output": "binned pixel size"       # Name this CoordinateSystem can be anything
    "scale": {3.0, 3.0, 3.0}
 }

 {
    "type": "image_pixel_size"
    "input": "image apix"
    "output": "binned pixel size"       # Name this CoordinateSystem can be anything
    "scale": {2.0, 2.0, 2.0}
 }

The first ``ImagePixelSize`` defines the image pixel size in terms of the base
logical coordinates system. The second defines it in terms of the physical pixel size
of the original image.  Either is correct but the first would be preferred as it is more
direct.

Because the second on starts at the "image apix" physical coordinate system
to get from the base logical coordinate system to "binned pixel size" you would first
have to apply the transformation for "image apix" coordinate system followed by the one
in this ``ImagePixelSize``.