"""Registers all durable-spine job handlers. Imported once at backend startup."""
import job_engine
import little_legacy_production as llp
import audiobook_video as abv


def register_all():
    job_engine.register("ll_pilot_render", llp.pilot_render_handler)
    job_engine.register("book_audiobook_video", abv._job_render)
    import book_manufacturing as bm
    job_engine.register("book_full_audiobook", bm.full_audiobook_handler)
    import manufacturing_engine as me
    job_engine.register("kr_manufacture_understanding", me.manufacture_handler)
