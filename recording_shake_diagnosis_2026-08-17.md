# Settings shake diagnosis — supplied recording

The recording shows the main workspace moving right when Settings opens and returning when it closes. The header, navigation tabs, and Generate Subtitles content all shift horizontally, which proves the drawer is still participating in the Streamlit document layout somewhere above the fixed visual panel. The visible slide effect is secondary; the root problem is a layout reflow caused by a drawer-related Streamlit block or its parent changing width/visibility.

The fix must keep both the Settings trigger anchor and the drawer host outside normal horizontal layout sizing. The host must be permanently present with a zero visual footprint or fixed-positioned, and the drawer panel itself must be fixed-positioned. Opening/closing must change only opacity/pointer-events or the panel's own transform, never the parent block's width, margin, display, or grid/flex participation.
