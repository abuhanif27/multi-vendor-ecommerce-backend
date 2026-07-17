from apps.catalog.models import (
    Category,
    CategoryAttribute,
)


class CategoryService:
    """
    Business logic related to categories.
    """

    @classmethod
    def get_attributes(
        cls,
        category: Category,
    ) -> list[CategoryAttribute]:
        """
        Return all active attributes available for a category,
        including inherited attributes from its ancestor categories.
        """

        lineage = []

        current = category

        while current is not None:
            lineage.append(current)
            current = current.parent

        attributes = []

        for category in reversed(lineage):
            attributes.extend(
                category.attributes.filter(
                    is_active=True,
                ).order_by(
                    "sort_order",
                    "created_at",
                )
            )

        return attributes
