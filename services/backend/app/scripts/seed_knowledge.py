"""Seed a starter RAG knowledge base across all collections.

Run with: python -m app.scripts.seed_knowledge

Uses the default embedder/Qdrant target from Settings (in-memory unless
QDRANT_URL points at a real server), so a plain in-process run only proves
the indexing path works — for persistent knowledge, point QDRANT_URL at a
running Qdrant instance first (see docker-compose.yml).
"""
import asyncio

from app.ai.rag.embeddings import HashingEmbedder
from app.ai.rag.rag_service import RAGService
from app.config import settings

DATASHEETS = [
    {
        "title": "STM32F103C8T6 Datasheet Summary",
        "source": "st.com",
        "content": (
            "STM32F103C8T6 is an ARM Cortex-M3 microcontroller running up to 72MHz "
            "with 64KB flash, 20KB SRAM, 2x SPI, 2x I2C, 3x USART, USB 2.0 full "
            "speed, and a 12-bit ADC. LQFP48 package. Common in blue pill boards."
        ),
        "metadata": {"part_number": "STM32F103C8T6", "manufacturer": "STMicroelectronics"},
    },
    {
        "title": "NE555 Timer Datasheet Summary",
        "source": "ti.com",
        "content": (
            "NE555 is a precision timing IC producing accurate delays and "
            "oscillation. Operates from 4.5V to 16V. Astable, monostable, and "
            "bistable modes. DIP-8 or SOIC-8 package."
        ),
        "metadata": {"part_number": "NE555", "manufacturer": "Texas Instruments"},
    },
]

STANDARDS = [
    {
        "title": "IPC-A-610 — Acceptability of Electronic Assemblies",
        "source": "ipc.org",
        "content": (
            "IPC-A-610 defines acceptability criteria for electronic assemblies, "
            "covering solder joints, component placement, and mechanical "
            "assembly across Class 1, 2, and 3 products."
        ),
        "metadata": {"standard": "IPC-A-610"},
    },
    {
        "title": "IPC-2221 — Generic PCB Design Standard",
        "source": "ipc.org",
        "content": (
            "IPC-2221 covers trace width vs current capacity, clearance rules, "
            "via sizing, and general design rules applicable across PCB "
            "technologies."
        ),
        "metadata": {"standard": "IPC-2221"},
    },
]

REFERENCE_DESIGNS = [
    {
        "title": "Buck Converter Reference Design (5V to 3.3V, 1A)",
        "source": "internal",
        "content": (
            "A synchronous buck converter stepping 5V down to 3.3V at 1A using "
            "a 2.2uH inductor, 22uF input/output capacitors, and a 500kHz "
            "switching frequency for compact layout."
        ),
        "metadata": {"category": "power"},
    },
]

APP_NOTES = [
    {
        "title": "Decoupling Capacitor Placement Best Practices",
        "source": "internal",
        "content": (
            "Place 100nF decoupling capacitors as close as possible to each IC "
            "power pin, with a low-inductance return path to the nearest "
            "ground via, to suppress high-frequency switching noise."
        ),
        "metadata": {"category": "layout"},
    },
]

COMPANY_KNOWLEDGE: list[dict] = []

COLLECTIONS = {
    "datasheets": DATASHEETS,
    "standards": STANDARDS,
    "reference_designs": REFERENCE_DESIGNS,
    "app_notes": APP_NOTES,
    "company_knowledge": COMPANY_KNOWLEDGE,
}


async def seed() -> None:
    rag = RAGService(embedder=HashingEmbedder(settings.embedding_dimensions))
    total = 0
    for collection, documents in COLLECTIONS.items():
        if not documents:
            continue
        total += await rag.index_documents(collection, documents)
    print(f"Indexed {total} documents across {len(COLLECTIONS)} collections.")


if __name__ == "__main__":
    asyncio.run(seed())
