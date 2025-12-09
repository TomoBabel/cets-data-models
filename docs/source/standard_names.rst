Standard Transformation and Coordinate System Names
===================================================

In order to maintain interoperability between different software packages standardised
names for some transformations and coordinate systems have been established.

Coorindate Systems
------------------

The starting coordinate systems are named "base_logical_coordinates_2D" and
base_logical_coordinates_3D. Global variables ``BASE_LOGICAL_COORDS_2D`` and
``BASE_LOGICAL_COORDS_3D`` contain these names. A helper function
``cets_data_model.standard_coordinate_systems.logical_coordinates()`` exists to
generate ``CoordinateSystem`` objects. If called without a name the base logical
coordinates system is returned by default.

Transformations
---------------

Standard transformation names and associated coordinate systems for various tasks are
found in ``src.cets_data_model.standard_names``. When these tasks are perfomed
the CETS data model objects recorded must conform to two rules:
 - The standard transformation names must be used for the transformation (or sequence of
   transformations) that accomplish the task
 - The output coordinate system of the transformation (or final transformation in a
   sequence) must have the standard coordinate system name for that task.

Global variables are to keep everything standarised.

Standard tasks
--------------

.. csv-table::
    :header: "Task", Transform name global,Coordinate system name global

    Set image pixel size,``IMAGE_PIXEL_SIZE_XFROM``, ``IMAGE_PIXEL_SIZE_COORDS``
    Set image super resolution pixel size,``IMAGE_PIXEL_SUPER_RES_SIZE_XFROM``,``IMAGE_SUPER_RES_PIXEL_SIZE_COORDS``"
    Align gain reference to movie frame,``ALIGN_CALIBRATION_IMAGE_XFROM``,``ALIGN_CALIBRATION_IMAGE_COORDS``
    Align movie frame to projection, ``ALIGN_MOVIE_FRAME_XFROM``, ``ALIGN_MOVIE_FRAME_COORDS``
    Align projection image to tomogram, ``ALIGN_PROJECTION_IMAGE_XFROM``, ``ALIGN_PROJECTION_IMAGE_COORDS``
    Align subtomogram to tomogram, ``ALIGN_SUBTOMOGRAM_XFROM``,``ALIGN_SUBTOMOGRAM_COORDS``
    Align map to tomogram, ``ALIGN_MAP_XFROM``, ``ALIGN_MAP_COORDS``
    Align annotation to tomogram, ``ALIGN_ANNOTATION_XFROM``, ``ALIGN_ANNOTATION_COORDS``

*Example*

A tilt image is aligned to a tomogram by an affine transformation. The resulting CETS
data object should contain:

.. code-block::

    Affine(
        name=ALIGN_PROJECTION_IMAGE_XFROM,
        input=BASE_LOGICAL_COORDS_3D,
        output=ALIGN_PROJECTION_IMAGE_COORDS,
        affine = <the affine matrix>
    )

The record for the image should then contain two ``CoordinateSystem`` objects, one for
the base 3D coordinates and one for after alignment. These can be generated easily with
the helper function:

.. code-block::

    # the base coordinate system
    logical_coords(dim=3)
    # the aligned coordinate system
    logical_coords(name=ALIGN_PROJECTION_IMAGE_COORDS, dim=3)


Transformation Helper Functions
-------------------------------

Some helper functions are provided in ``cets_data_models.standard_transformations``
to make it easy to generate the scale transformations and their associated coordinate systems
wth the correct naming conventions.

