# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later


"""Models for the schemes app."""

from django.db import models


class ImageScheme(models.Model):
    """Main model for rhythm scheme image.

    Attributes:
        code (str): special name of scheme
        inscription (str): title of image
        height (int): original image height
        width (int): original image width
        image (image): image file path
    """

    code = models.CharField(
        "Кодовое название",
        help_text="Позволяет указать, для какого именно урока и что это за рисунок",
        max_length=20,
        unique=True,
    )
    inscription = models.CharField("Надпись", max_length=100, blank=True)
    height = models.PositiveIntegerField("Высота", blank=True, null=True)
    width = models.PositiveIntegerField("Ширина", blank=True, null=True)
    image = models.ImageField(
        "Изображение",
        upload_to="lesson_schemes/",
        height_field="height",
        width_field="width",
        max_length=255,
    )

    class Meta:
        verbose_name = "Бой или схема (рисунок)"
        verbose_name_plural = "Бои или схемы (рисунки)"

    def __str__(self) -> str:
        return f"{self.code}: {self.inscription}"
