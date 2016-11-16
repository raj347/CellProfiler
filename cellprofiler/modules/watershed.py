"""

<strong>Watershed</strong>

Watershed is a segmentation algorithm. It is used to separate different objects in an image.

"""

import cellprofiler.image
import cellprofiler.module
import cellprofiler.object
import cellprofiler.setting
import mahotas
import numpy
import scipy.ndimage
import skimage.feature
import skimage.measure
import skimage.morphology


class Watershed(cellprofiler.module.ImageSegmentation):
    module_name = "Watershed"

    variable_revision_number = 1

    def create_settings(self):
        super(Watershed, self).create_settings()

        self.operation = cellprofiler.setting.Choice(
            "Generate from",
            [
                "Distance",
                "Markers"
            ],
            "Distance",
            doc="""Select a method of inputs for the watershed algorithm:
            <ul>
                <li>
                    <i>Distance</i> (default): This is classical nuclei segmentation using watershed. Your "Input" image
                    should be a binary image. Markers and other inputs for the watershed algorithm will be
                    automatically generated.
                </li>
                <br>
                <li>
                    <i>Markers</i>: Use manually generated markers and supply an optional mask for watershed. Watershed
                    works best when the "Input" image has high intensity surrounding regions of interest and low intensity
                    inside regions of interest. Refer to the documentation for the other available options for more
                    information.
                </li>
            </ul>
            """
        )

        self.markers_name = cellprofiler.setting.ImageNameSubscriber(
            "Markers",
            doc="An image marking the approximate centers of the objects for segmentation."
        )

        self.mask_name = cellprofiler.setting.ImageNameSubscriber(
            "Mask",
            can_be_blank=True,
            doc="Optional. Only regions not blocked by the mask will be segmented."
        )

        self.radius = cellprofiler.setting.Integer(
            minval=1,
            text="Diameter",
            value=16,
        )

    def settings(self):
        __settings__ = super(Watershed, self).settings()

        return __settings__ + [
            self.operation,
            self.markers_name,
            self.mask_name,
            self.radius
        ]

    def visible_settings(self):
        __settings__ = super(Watershed, self).settings()

        __settings__ = __settings__ + [
            self.operation
        ]

        if self.operation.value == "Distance":
            __settings__ = __settings__ + [
                self.radius
            ]
        else:
            __settings__ = __settings__ + [
                self.markers_name,
                self.mask_name
            ]

        return __settings__

    def run(self, workspace):
        x_name = self.x_name.value

        y_name = self.y_name.value

        images = workspace.image_set

        x = images.get_image(x_name)

        dimensions = x.dimensions

        x_data = x.pixel_data

        if self.operation.value == "Distance":
            distance = mahotas.distance(x_data)

            distance = mahotas.stretch(distance)

            radius = self.radius.value

            if x.dimensions is 2:
                shape = (radius, radius)
            else:
                shape = (radius, radius, radius)

            footprint = numpy.ones(shape)

            peaks = mahotas.morph.regmax(distance, footprint)

            markers, count = mahotas.label(peaks, footprint)

            surface = distance.max() - distance

            y_data = mahotas.cwatershed(surface, markers)

            y_data *= x_data
        else:
            markers_name = self.markers_name.value

            markers = images.get_image(markers_name)

            data = x_data

            markers_data = markers.pixel_data

            mask_data = None

            if not self.mask_name.is_blank:
                mask_name = self.mask_name.value

                mask = images.get_image(mask_name)

                mask_data = mask.pixel_data

            y_data = skimage.morphology.watershed(
                image=data,
                markers=markers_data,
                mask=mask_data
            )

        y_data = skimage.measure.label(y_data)

        objects = cellprofiler.object.Objects()

        objects.segmented = y_data

        objects.parent_image = x

        workspace.object_set.add_objects(objects, y_name)

        if self.show_window:
            workspace.display_data.x_data = x_data

            workspace.display_data.y_data = y_data

            workspace.display_data.dimensions = dimensions
