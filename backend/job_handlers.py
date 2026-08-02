"""Registers all durable-spine job handlers. Imported once at backend startup."""
import job_engine
import little_legacy_production as llp
import audiobook_video as abv


def register_all():
    job_engine.register("ll_pilot_render", llp.pilot_render_handler)
    job_engine.register("book_audiobook_video", abv._job_render)
