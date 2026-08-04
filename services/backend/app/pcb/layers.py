from enum import Enum


class LayerType(str, Enum):
    TOP_COPPER = "top_copper"
    BOTTOM_COPPER = "bottom_copper"
    INNER_COPPER_1 = "inner_copper_1"
    INNER_COPPER_2 = "inner_copper_2"
    INNER_COPPER_3 = "inner_copper_3"
    INNER_COPPER_4 = "inner_copper_4"
    SOLDER_MASK_TOP = "solder_mask_top"
    SOLDER_MASK_BOTTOM = "solder_mask_bottom"
    SILKSCREEN_TOP = "silkscreen_top"
    SILKSCREEN_BOTTOM = "silkscreen_bottom"
    PASTE_TOP = "paste_top"
    PASTE_BOTTOM = "paste_bottom"
    KEEPOUT = "keepout"


# Inner copper layers used for a given layer count, outermost-in. A 2-layer
# board is just top+bottom; higher counts add inner planes in pairs.
_INNER_LAYERS_BY_COUNT: dict[int, list[LayerType]] = {
    2: [],
    4: [LayerType.INNER_COPPER_1, LayerType.INNER_COPPER_2],
    6: [
        LayerType.INNER_COPPER_1,
        LayerType.INNER_COPPER_2,
        LayerType.INNER_COPPER_3,
        LayerType.INNER_COPPER_4,
    ],
}


def copper_layers_for_count(layers_count: int) -> list[LayerType]:
    """Copper layer stack for a board with the given layer count.

    Boards with an unlisted count (e.g. 8, 16) fall back to the nearest
    defined stack padded with numbered inner planes — real stack-up design
    (impedance targeting, plane assignment) is a manufacturing-partner
    conversation, not something this function can decide for the user.
    """
    inner = _INNER_LAYERS_BY_COUNT.get(layers_count)
    if inner is None:
        pair_count = max(0, (layers_count - 2) // 2)
        inner = [LayerType.INNER_COPPER_1, LayerType.INNER_COPPER_2][: pair_count * 2]
    return [LayerType.TOP_COPPER, *inner, LayerType.BOTTOM_COPPER]
