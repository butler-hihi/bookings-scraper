# BookingsScraperV1

SANParks trail booking availability monitoring system.

## Features

- 🔍 Monitor SANParks trail availability (Otter Trail, more coming)
- 📊 Track changes over time with SQLite persistence  
- 🔔 WhatsApp notifications for availability changes
- ⚡ Runs every minute with minimal overhead
- 📁 Clean, modular, production-ready architecture
- 🛠️ Easy to extend with new trails

## Architecture

```
src/bookings_scraper/
├── main.py          # Entry point
├── scheduler.py     # Scheduling logic
├── database.py      # SQLite operations
├── notifier.py      # WhatsApp notifications
└── trails/
    ├── base.py      # Abstract base class
    └── otter.py     # Otter Trail implementation
```

## Quick Start

```bash
# Install dependencies
cd BookingsScraperV1
python3 -m pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Run the scraper
python3 src/bookings_scraper/main.py
```

## Configuration

Edit `config/trails.yaml` to add or modify trails.

## API

This project uses the official SANParks HTML interface:
- **Endpoint**: `https://www2.sanparks.org/campground/otter/`
- **Method**: HTML parsing (no public API key available)

Note: SANParks may block automated scraping. Consider:
1. Adding proper User-Agent headers
2. Implementing delays between requests
3. Using a rotating proxy if needed
4. Obtaining explicit permission from SANParks

## Running

```bash
# Single check
python3 src/bookings_scraper/main.py --once

# Run as service (background)
python3 src/bookings_scraper/main.py --service

# Custom interval (e.g., every 120 seconds)
python3 src/bookings_scraper/main.py --interval 120
```

## Extending

To add a new trail:

1. Add entry to `config/trails.yaml`
2. Create `src/bookings_scraper/trails/{trail_name}.py`
3. Inherit from `src/bookings_scraper/trails/base.py`

## Example Output

```
📍 Otter Trail Availability Update

🟢 Newly Available:
- 2026-04-15
- 2026-04-16

🔴 No Longer Available:
- 2026-04-01

⏱ Checked at: 2026-03-30 14:01
```

## License

Private - for internal use only.
