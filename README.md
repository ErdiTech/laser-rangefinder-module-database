# Laser rangefinder module database

An open, machine-readable dataset of **single-point laser rangefinder / LiDAR distance modules** (UART, I2C, CAN, analog) used in drones, robots, industrial measurement and IoT. 109 modules from 8 manufacturers, every value copied from the manufacturer's own public page and stamped with the capture date.

Use it to compare range, accuracy, update rate, interface, weight and public price across brands without opening fifty datasheets.

- `data/modules.json` — one object per module (schema below)
- `data/modules.csv` — the same rows for spreadsheets / pandas
- `data/schema.json` — field list
- `scripts/validate.py` — checks every row has every field and that numbers are numbers

## Coverage

| Manufacturer | Modules |
|---|---|
| ERDI LASER (ERDI TECH LTD) | 59 |
| Benewake | 12 |
| LightWare | 12 |
| JRT | 10 |
| Nooploop | 8 |
| Lumispot Tech | 4 |
| Garmin | 2 |
| DFRobot | 2 |

## Schema

| Field | Meaning |
|---|---|
| `brand` | Manufacturer as written on its site |
| `model` | Model name as written on its site |
| `wavelength_nm` | Laser wavelength (905 = silicon APD class, 1535 = eye-safe InGaAs class) |
| `min_range_m` / `max_range_m` | Published range limits in metres |
| `range_condition` | Target and conditions the max range is quoted for (a range number without a target is not comparable) |
| `accuracy` | Published accuracy string, kept verbatim because vendors quote it differently (±cm, % of range, RMS) |
| `rate_hz` | Measurement / output rate |
| `interface` | Electrical interfaces listed by the vendor |
| `voltage` | Supply voltage |
| `weight_g` | Weight in grams |
| `dimensions` | L × W × H as published |
| `laser_class` | IEC 60825-1 class if published |
| `price_public_usd` | Public single-unit price if the vendor publishes one; `null` if the vendor only quotes |
| `product_url` / `source_url` | Where the values came from |
| `captured_at` | Date the page was read |

`null` means the vendor does not publish the value, not that the module lacks it.

## Quick start

```python
import json, pandas as pd
df = pd.DataFrame(json.load(open("data/modules.json")))
print(df[df.max_range_m >= 1000].sort_values("weight_g")[["brand","model","max_range_m","weight_g","price_public_usd"]])
```

```bash
python scripts/validate.py          # exits non-zero on a bad row
```

## Modules by manufacturer

### ERDI LASER (ERDI TECH LTD)

| Model | Wavelength | Max range | Accuracy | Rate | Interface | Weight | Public price | Source |
|---|---|---|---|---|---|---|---|---|
| MINI-100 | 1535 nm |  |  |  |  | 2.5 g | $100 | [page](https://erdilrf.com/models/mini-100/) |
| ER100 |  |  |  |  |  | 7.0 g | $70 | [page](https://erdilrf.com/models/er100/) |
| ER10000 | 1535 nm |  |  |  |  | 220.0 g | $5000 | [page](https://erdilrf.com/models/er10000/) |
| ER200 | 1535 nm |  |  |  |  | 7.0 g | $80 | [page](https://erdilrf.com/models/er200/) |
| ER2000 | 1535 nm |  |  |  |  | 105.0 g | $1500 | [page](https://erdilrf.com/models/er2000/) |
| ER300 | 1535 nm |  |  |  |  | 8.5 g | $100 | [page](https://erdilrf.com/models/er300/) |
| ER400 | 1535 nm |  |  |  |  | 12.0 g | $200 | [page](https://erdilrf.com/models/er400/) |
| ER4000 | 1535 nm |  |  |  |  | 105.0 g | $2000 | [page](https://erdilrf.com/models/er4000/) |
| ER500 | 1535 nm |  |  |  |  | 12.0 g | $240 | [page](https://erdilrf.com/models/er500/) |
| ER800 | 1535 nm |  |  |  |  | 18.0 g | $1050 | [page](https://erdilrf.com/models/er800/) |
| ER8000 | 1535 nm |  |  |  |  | 220.0 g | $3000 | [page](https://erdilrf.com/models/er8000/) |
| ER900 | 1535 nm |  |  |  |  | 18.0 g | $1050 | [page](https://erdilrf.com/models/er900/) |
| LRF1829C | 1535 nm |  | ±2 m | 0.5Hz ~10Hz | RS422 | 400.0 g | $3500 | [page](https://erdilrf.com/models/lrf1829c/) |
| LRF10VB | 940 nm | 9.0 m | ±5 cm (<5 m); 1% (≥5 m) | 50 Hz | UART | 1.0 g | $6 | [page](https://erdilrf.com/models/lrf10vb/) |
| LRF22VB | 905 nm | 20.0 m | ±5 cm (<5 m); 1% (≥5 m) | 200 Hz (alternatives: 100/50/20/10/1 Hz) | UART/IIC | 1.5 g | $8 | [page](https://erdilrf.com/models/lrf22vb/) |
| LRF50H | 905 nm | 50.0 m | ±5 cm (<10 m); 1% (≥10 m), 2σ | 20 Hz-10 kHz (default: 1 kHz) | UART | 15.0 g | $50 | [page](https://erdilrf.com/models/lrf50h/) |
| LRF50VB | 905 nm | 50.0 m | ±5 cm (<5 m); 1% (≥5 m) | 100 Hz | UART/IIC | 1.3 g | $20 | [page](https://erdilrf.com/models/lrf50vb/) |
| LRF100H | 905 nm | 100.0 m | ±10 cm (<10 m); 1% (≥10 m) | 20 Hz-10 kHz (default: 1 kHz) | UART, IIC | 20.0 g | $80 | [page](https://erdilrf.com/models/lrf100h/) |
| LRF200H | 905 nm | 200.0 m | ±10 cm (<10 m); 1% (≥10 m) | 20 Hz-10 kHz (default: 1 kHz) | UART, IIC | 20.0 g | $100 | [page](https://erdilrf.com/models/lrf200h/) |
| LRF300H | 905 nm | 300.0 m | ±10 cm (<10 m); 1% (≥10 m) | 1 kHz or 50 Hz (automatically switched to match reflected-signal intensity) | UART, IIC | 20.0 g | $140 | [page](https://erdilrf.com/models/lrf300h/) |
| LRF600H | 905 nm | 600.0 m | ±10 cm (<10 m); 1% (≥10 m) | 1 kHz or 50 Hz (automatically switched to match reflected-signal intensity) | UART/IIC | 20.0 g | $160 | [page](https://erdilrf.com/models/lrf600h/) |
| LR1000E2 | 905 nm | 1000.0 m | ±1 m (D ≤ 400 m); ±(1 + 0.001D) m (D > 400 m) | 3–10 Hz (adaptive) | UART-TTL | 10.0 g | $30 | [page](https://erdilrf.com/models/lr1000e2/) |
| LR1000E4 | 905 nm | 1000.0 m | ±1 m (D ≤ 400 m); ±(1 + 0.001D) m (D > 400 m) | 3–10 Hz (adaptive) | UART-TTL | 10.0 g | $30 | [page](https://erdilrf.com/models/lr1000e4/) |
| SPD1200N3 | 905 nm | 1000.0 m | ±0.5 m at d ≤100 m; ±(0.5 m + 0.00075d) for 100 m < d <1000 m | 2.5–15 Hz | UART, 3.3 V TTL; customizable | 6.0 g | $36 | [page](https://erdilrf.com/models/spd1200n3/) |
| LR1000D23 | 905 nm | 1200.0 m | δ ≤ 100 cm, 5 m ≤ d < 1000 m¹) (Standard version: ±1 m) | 3 Hz – 12 Hz (customizable) | UART-TTL, customizable | 20.0 g | $110 | [page](https://erdilrf.com/models/lr1000d23/) |
| LR1200D23 | 905 nm | 1200.0 m | δ ≤ ±1 m, 4 m ≤ d < 1000 m¹) (Standard version: ±1 m) | 2–10 Hz | UART - TTL, customizable | 20.0 g | $130 | [page](https://erdilrf.com/models/lr1200d23/) |
| LR1200E2 | 905 nm | 1200.0 m | Both sources give ±1 m (6 m ≤ D < 500 m) and ±(0.5 m + 0.001D) for the second interval. The archived factory pack table ends the second interval at 1,000 m; the current official public PDF v1.2 lists 500 m ≤ D ≤ 1,200 m. Sources differ; confirm the applicable supplied revision. | 2–10 Hz (adaptive) | UART-TTL | 10.0 g | $35 | [page](https://erdilrf.com/models/lr1200e2/) |
| LR1200E4 | 905 nm | 1200.0 m | ±1 m (D ≤ 400 m); ±(1 + 0.001D) m (D > 400 m) | 2–10 Hz (adaptive) | UART-TTL | 10.0 g | $35 | [page](https://erdilrf.com/models/lr1200e4/) |
| LRF1200A1 | 905 nm | 1200.0 m | ±1 m (5 m ≤ L ≤ 100 m); ±(1 + 0.004L) m (L > 100 m) | 1–3 Hz | UART, 3.3 V TTL | 18.0 g | $35 | [page](https://erdilrf.com/models/lrf1200a1/) |
| SPD1200ZG | 905 nm | 1200.0 m | ±0.5 m at d ≤100 m; ±(0.5 m + 0.0007d) for 100 m < d <1200 m | 2–10 Hz | UART-TTL; customizable | 5.0 g | $80 | [page](https://erdilrf.com/models/spd1200zg/) |
| LR1500D23 | 905 nm | 1500.0 m | δ ≤ ±1 m, 4 m ≤ d < 1000 m¹) (Standard version: ±1 m) | 2–10 Hz | UART - TTL, customizable | 20.0 g | $140 | [page](https://erdilrf.com/models/lr1500d23/) |
| LR1500E2 | 905 nm | 1500.0 m | Both sources give ±1 m (6 m ≤ D < 500 m) and ±(0.5 m + 0.001D) for the second interval. The archived factory pack table ends the second interval at 1,000 m; the current official public PDF v1.2 lists 500 m ≤ D ≤ 1,500 m. Sources differ; confirm the applicable supplied revision. | 2–10 Hz (adaptive) | UART-TTL | 10.0 g | $40 | [page](https://erdilrf.com/models/lr1500e2/) |
| LR1500E4 | 905 nm | 1500.0 m | ±1 m (D ≤ 400 m); ±(1 + 0.001D) m (D > 400 m) | 2–10 Hz (adaptive) | UART-TTL | 10.0 g | $40 | [page](https://erdilrf.com/models/lr1500e4/) |
| LRF1500H | 905 nm | 1500.0 m | ±10 cm (<10 m); 1% (≥10 m) | 1 kHz or 50 Hz (automatically switched to match reflected-signal intensity) | UART/IIC | 20.0 g | $180 | [page](https://erdilrf.com/models/lrf1500h/) |
| SPD1200N0 | 905 nm | 1500.0 m | ±0.3 m (D ≤100 m); ±0.3 m + D × 0.7‰ (100 m < D <1200 m) | 2–15 Hz or 4–15 Hz, adaptive | UART-TTL (customizable) | 5.0 g | $35 | [page](https://erdilrf.com/models/spd1200n0/) |
| SPD1200N2 | 905 nm | 1500.0 m | ±0.3 m (D ≤100 m); ±0.3 m + D × 0.7‰ (100 m < D <1200 m) | 2–15 Hz or 4–15 Hz, adaptive | UART-TTL (customizable) | 5.0 g | $35 | [page](https://erdilrf.com/models/spd1200n2/) |
| SPD1200N4 | 905 nm | 1500.0 m | ±0.3 m (D ≤100 m); ±0.3 m + D × 0.7‰ (100 m < D <1200 m) | 2–15 Hz or 4–15 Hz, adaptive | UART-TTL (customizable) | 5.0 g | $35 | [page](https://erdilrf.com/models/spd1200n4/) |
| SPD1200S2 | 905 nm | 1500.0 m | ±0.3m (≤400m)±0.5m + d×0.1% (400m＜d＜1200m) | 4Hz~15Hz Adaptive | UART-TTL, Customizable | 10.0 g | $150 | [page](https://erdilrf.com/models/spd1200s2/) |
| SPD1200Z2 | 905 nm | 1500.0 m | Current published table and archived factory PDF: ±0.2 m (d≤200 m); ±0.5 m (d≤400 m); ±(0.5 m + 0.001d) (400 m<d<1,200 m). Archived factory DOCX: ±0.3 m (d≤100 m); ±(0.3 m + 0.0007d) (100 m<d<1,200 m). Sources differ; confirm the supplied configuration. d is distance in metres. | Current published table and archived factory PDF technical table: 2–20 Hz adaptive. Archived PDF overview: 2–15 Hz; its continuous-mode section gives typical 2 Hz and maximum 15 Hz. Archived factory DOCX technical table: 2–20 Hz; its continuous-mode section gives typical 2 Hz and maximum 20 Hz. Confirm the supplied mode/configuration; sources differ. | UART-TTL, Customizable | 6.0 g | $150 | [page](https://erdilrf.com/models/spd1200z2/) |
| LR2000E2 | 905 nm | 2000.0 m | ±1 m (D ≤ 400 m); 0.4% of D (400 m < D ≤ 2000 m) | 2–10 Hz (adaptive) | UART-TTL |  | $50 | [page](https://erdilrf.com/models/lr2000e2/) |
| LR2000E4 | 905 nm | 2000.0 m | ±1 m (D ≤ 400 m); 0.4% of D (400 m < D ≤ 2000 m) | 2–10 Hz (adaptive) | UART-TTL |  | $50 | [page](https://erdilrf.com/models/lr2000e4/) |
| LRF0105C | 1535 nm | 3000.0 m | ±2 m | Single, 1Hz, 5Hz, 10Hz |  | 29.0 g | $300 | [page](https://erdilrf.com/models/lrf0105c/) |
| LRF0310C | 1535 nm | 3000.0 m | ±1 m | Single, 1Hz ~10Hz |  | 32.0 g | $300 | [page](https://erdilrf.com/models/lrf0310c/) |
| LRF3000A1 | 905 nm | 3000.0 m | ±0.7 m (D ≤ 100 m); ±(0.7 + 0.003D) m (D > 100 m) | Normal: 3–10 Hz; long-range: 1–10 Hz | UART, 3.3 V TTL | 12.0 g | $80 | [page](https://erdilrf.com/models/lrf3000a1/) |
| LRF0305C | 1535 nm | 4000.0 m | ±1 m | 1Hz ~10Hz | UART(TTL 3.3V) | 14.0 g | $300 | [page](https://erdilrf.com/models/lrf0305c/) |
| LRF0306C | 1535 nm | 4000.0 m | ±1 m | 1Hz ~3Hz | UART(TTL 3.3V) | 14.0 g | $300 | [page](https://erdilrf.com/models/lrf0306c/) |
| LRF0405C | 1535 nm | 6000.0 m | +/-2 m | Single measurement or 1 to 10 Hz | UART, 3.3 V TTL level | 32.0 g | $400 | [page](https://erdilrf.com/models/lrf0405c/) |
| LRF0609C | 1535 nm | 6000.0 m | ≤ ±2 m |  | TTL |  | $800 | [page](https://erdilrf.com/models/lrf0609c/) |
| LRF0610C | 1535 nm | 6000.0 m | ±2 m | 0.5Hz ~10Hz | TTL: Molex 51021-0500; RS-422: J30J. Confirm the ordered version. | 90.0 g | $700 | [page](https://erdilrf.com/models/lrf0610c/) |
| LRF0612C | 1535 nm | 6000.0 m | ±2 m | 1Hz ~10Hz |  | 58.0 g | $700 | [page](https://erdilrf.com/models/lrf0612c/) |
| LRF0815C | 1535 nm | 8000.0 m | ±2 m | 0.5 to 10 Hz |  | 175.0 g | $900 | [page](https://erdilrf.com/models/lrf0815c/) |
| LRF0816C | 1535 nm | 8000.0 m | ±2 m | 1Hz ~10Hz |  | 58.0 g | $1200 | [page](https://erdilrf.com/models/lrf0816c/) |
| LRF0818C | 1535 nm | 8000.0 m | ≤ ±2 m |  | TTL |  | $900 | [page](https://erdilrf.com/models/lrf0818c/) |
| LRF1017C |  | 10000.0 m | ±2 m | 0.5Hz ~10Hz | RS422 | 275.0 g | $1300 | [page](https://erdilrf.com/models/lrf1017c/) |
| LRF1221C |  | 12000.0 m | ±2 m | 0.5Hz ~10Hz | RS422 | 275.0 g | $1300 | [page](https://erdilrf.com/models/lrf1221c/) |
| LRF1222C |  | 12000.0 m | ±2 m | 0.5Hz ~10Hz | RS422 | 335.0 g | $1300 | [page](https://erdilrf.com/models/lrf1222c/) |
| LRF1525C |  | 15000.0 m | ±2 m | 0.5Hz ~10Hz | RS422 | 400.0 g | $3000 | [page](https://erdilrf.com/models/lrf1525c/) |
| LRF1831C | 1535 nm | 15000.0 m | ±2 m | 0.5Hz ~10Hz | RS422 | 410.0 g | $3500 | [page](https://erdilrf.com/models/lrf1831c/) |
| LRF1830C |  | 23000.0 m | ±2 m | 0.5–10 Hz | RS-422 in the specification table; TTL/RS-422 alternatives in the interface section |  | $3500 | [page](https://erdilrf.com/models/lrf1830c/) |

### Benewake

| Model | Wavelength | Max range | Accuracy | Rate | Interface | Weight | Public price | Source |
|---|---|---|---|---|---|---|---|---|
| TF-Luna |  | 8 m | ± 6 cm @ (0.2 ~ 3 m) | 1 ~ 250 Hz | UART, I/O, I²C | 5.0 g |  | [page](https://en.benewake.com/TFLuna/index.html) |
| TFmini-S |  | 12 m | ± 6 cm within 0.1 ~ 6 m | 1 ~ 1000 Hz | UART, I/O, I²C | 5.0 g |  | [page](https://en.benewake.com/TFminiS/index.html) |
| TFmini Plus |  | 12 m | ± 5 cm @ (0.1 ~ 5 m) | 1 ~ 1000 Hz | UART, I/O, I²C | 12.0 g |  | [page](https://en.benewake.com/TFminiPlus/index.html) |
| TFmini-i |  | 12 m |  | 1 ~ 1000 Hz | CAN, RS-485 | 52 g |  | [page](https://en.benewake.com/TFminii/index.html) |
| TF-NOVA |  | 14 m |  | 1 ~ 900 Hz | UART, I/O, I²C |  |  | [page](https://en.benewake.com/tf-nova) |
| TFS20-L |  | 20 m |  | 1 ~ 250 Hz | UART, I²C | 1.35 g |  | [page](https://en.benewake.com/TFS20L/index.html) |
| TF02-Pro |  | 40 m |  | 1 ~ 1000 Hz | UART, I/O, I²C | 50 g |  | [page](https://en.benewake.com/TF02Pro/index.html) |
| TF02-i |  | 40 m |  | 1 ~ 1000 Hz | CAN, RS-485 | 60 g |  | [page](https://en.benewake.com/TF02i/index.html) |
| TFA170-L |  | 170 m |  | 1 ~ 1000 Hz | RS-232 | 10.0 g |  | [page](https://en.benewake.com/TFA170L/index.html) |
| TF03-100/180 |  | 180 m |  | 1 ~ 9800 Hz | UART, CAN, RS-232, RS-485 | 86.0 g |  | [page](https://en.benewake.com/TF03/index.html) |
| TFA300 Series |  | 290 m | ± 10 cm (< 10 m) 1% (≥ 10 m) | 1 ~ 10,000 Hz | UART, CAN | 10.5 g |  | [page](https://en.benewake.com/TFA300/index.html) |
| TF350 |  | 350 m |  | 1 ~ 1000 Hz | UART, CAN, RS-232, RS-485 | 224.0 g |  | [page](https://en.benewake.com/TF350/index.html) |

### LightWare

| Model | Wavelength | Max range | Accuracy | Rate | Interface | Weight | Public price | Source |
|---|---|---|---|---|---|---|---|---|
| SF000/B | 905 nm | 50 m |  | 48 to 388 readings per second | Serial UART and I2C (3.3 V TTL, 5 V tolerant) | 9.8 g | $319 | [page](https://lightwarelidar.com/shop/sf000-b/) |
| SF23/B | 905 nm | 50 m |  | 1 to 20 readings per second | Serial UART (3.0V logic), shutdown and control | 6.5 g | $59 | [page](https://lightwarelidar.com/shop/sf23-b/) |
| SF45/B (scanning) | 905 nm | 50 m |  | Up to 5,000 readings per second and 5 sweeps per second | USB, Serial UART and I2C (3.3 V TTL, 5 V tolerant) | 59 g | $519 | [page](https://lightwarelidar.com/shop/sf45-b/) |
| LW20/C | 905 nm | 100 m |  | 48 to 5 000 readings per second | Serial UART and I2C (3.3 V TTL, 5 V tolerant) | 19.5 g | $349 | [page](https://lightwarelidar.com/shop/lw20-c/) |
| LW20/HA | 905 nm | 100 m | Better than 1cm over 100m | 48 to 1 250 readings per second | Serial UART and I2C (3.3 V TTL, 5 V tolerant) | 19.5 g | $389 | [page](https://lightwarelidar.com/shop/lw20-ha/) |
| SF20/C | 905 nm | 100 m |  | 48 to 5 000 readings per second | USB, Serial UART and I2C (3.3 V TTL, 5 V tolerant) | 7.5 g | $319 | [page](https://lightwarelidar.com/shop/sf20-c/) |
| SF20/HA | 905 nm | 100 m | Better than 1cm over 100m | 48 to 1 250 readings per second | USB, Serial UART and I2C (3.3 V TTL, 5 V tolerant) | 7.5 g | $359 | [page](https://lightwarelidar.com/shop/sf20-ha/) |
| SF30/C | 905 nm | 100 m |  | 39 to 20 000 readings per second | USB, Serial UART (3.3 V TTL, 5 V tolerant) | 30 g | $349 | [page](https://lightwarelidar.com/shop/sf30-c/) |
| SF11/C | 905 nm | 100 m |  | 20 readings per second | USB, Serial UART and I2C (3.3 V TTL, 5 V tolerant) | 30 g | $199 | [page](https://lightwarelidar.com/shop/sf11-c-100-m2/) |
| SF30/D | 905 nm | 200 m |  | 39 to 20 000 readings per second | USB, Serial UART and I2C (3.3 V TTL, 5 V tolerant) | 30 g | $459 | [page](https://lightwarelidar.com/shop/sf30-d/) |
| GRF-250 | 905 nm | 250 m | ± 50 cm (1 sigma) | 1 to 50 readings per second | USB, Serial UART and I2C (3.3 V TTL, 5 V tolerant) | 10.7 g | $399 | [page](https://lightwarelidar.com/shop/grf-250/) |
| GRF-500 | 905 nm | 500 m | ± 50 cm (1 sigma) | 0.5 to 10 readings per second | USB, Serial UART and I2C (3.3 V TTL, 5 V tolerant) | 10.7 g | $459 | [page](https://lightwarelidar.com/shop/grf-500/) |

### Garmin

| Model | Wavelength | Max range | Accuracy | Rate | Interface | Weight | Public price | Source |
|---|---|---|---|---|---|---|---|---|
| LIDAR-Lite v3 | 905 nm | 40 m | ±2.5 cm (1 in.) typical (<5 m); ±10 cm (3.9 in.) typical (>=5 m) | 270 Hz typical; 650 Hz fast mode; >1000 Hz short range only | I2C, PWM | 22 g | $149.99 | [page](https://static.garmin.com/pumac/LIDAR_Lite_v3_Operation_Manual_and_Technical_Specifications.pdf) |
| LIDAR-Lite v3HP | 905 nm | 40 m | ±1 cm (0.4 in.) (<2 m); ±5 cm (2 in.) typical (>=2 m) |  | I2C, PWM | 38 g |  | [page](https://static.garmin.com/pumac/LIDAR-Lite_v3HP_Instructions_EN.pdf) |

### Nooploop

| Model | Wavelength | Max range | Accuracy | Rate | Interface | Weight | Public price | Source |
|---|---|---|---|---|---|---|---|---|
| TOFSense-M S (8x8 array) |  | 4 m | ±1.5cm | 15Hz@8*8; 60Hz@4*4 | UART, CAN | 5.8 g |  | [page](https://www.nooploop.com/lidar/) |
| TOFSense-F2 Mini |  | 7.8 m | ±4.0cm | 50Hz | UART, IIC, I/O | 1.0 g |  | [page](https://www.nooploop.com/lidar/) |
| TOFSense |  | 8 m | ±1.5cm@[0.03, 1.0]m; ±3.0cm@(1.0, 8.0]m | 30Hz | UART, CAN, I/O | 2.7 g |  | [page](https://www.nooploop.com/lidar/) |
| TOFSense-UART |  | 8 m | ±1.5cm@[0.03, 1.0]m; ±3.0cm@(1.0, 8.0]m | 30Hz | UART, I/O | 2.7 g |  | [page](https://www.nooploop.com/lidar/) |
| TOFSense S |  | 8 m | ±1.5cm@[0.03, 1.0]m; ±3.0cm@(1.0, 8.0]m | 30Hz | UART, CAN | 5.8 g |  | [page](https://www.nooploop.com/lidar/) |
| TOFSense-F2 |  | 25 m | ±3.0cm | 100Hz | UART, IIC, I/O | 7.5 g |  | [page](https://www.nooploop.com/lidar/) |
| TOFSense-F2 P |  | 50 m | ±3.0cm | 100Hz | UART, IIC, I/O | 7.5 g |  | [page](https://www.nooploop.com/lidar/) |
| TOFSense-F2 PH |  | 50 m | ±3.0cm | 100Hz | UART, IIC, I/O |  |  | [page](https://www.nooploop.com/lidar/) |

### JRT

| Model | Wavelength | Max range | Accuracy | Rate | Interface | Weight | Public price | Source |
|---|---|---|---|---|---|---|---|---|
| ETYS-HF-2 | 905 nm | 150 m | <=0.1m (0.1-2m); 5%×L (>2m) | 20Hz-10KHz |  | 45.0 g |  | [page](https://www.jrt-measure.com/10000hz-high-frequency-lidar-module/68823895.html) |
| PTGC-10X-1 | 905 nm | 1000 m | 5<=L<=100m: ±0.7m | 1-3Hz | UART-TTL (3.3V) | 25.0 g |  | [page](https://www.jrt-measure.com/laser-rangefinder-sensor/68652130.html) |
| PTGL-12X-1 | 905 nm | 1200 m | d <= 100 m: ±0.3 m; d > 100 m: ±(0.4 + 0.006 × d) m | 2 Hz – 15 Hz (Adaptive) | UART (TTL_3.3V) | 6.0 g | $49 | [page](https://www.jrt-measure.com/905nm-laser-rangefinder-module/68788230.html) |
| PTGL2-12X-1 | 905 nm | 1200 m | d <= 100m: ±0.3m; d >= 100m: ±(0.3 + 0.0007 × D) | 2Hz–30Hz (adaptive) | UART (TTL 3.3V) | 6.0 g |  | [page](https://www.jrt-measure.com/905nm-laser-rangefinder-module/69008485.html) |
| PTGC-12X-2 | 905 nm | 1200 m | 5<=L<=100m: ±0.7m | 1-3Hz | UART-TTL (3.3V) | 22.0 g |  | [page](https://www.jrt-measure.com/905nm-laser-rangefinder-module/68768255.html) |
| PTGS-12X-1 | 905 nm | 1200 m |  |  |  | 12.0 g |  | [page](https://www.jrt-measure.com/905nm-laser-rangefinder-module/68713654.html) |
| ETYU-20X-1 | 1535 nm | 2000 m | <=±1m | Single shot, 1Hz-10Hz | RS422 | 190.0 g |  | [page](https://www.jrt-measure.com/industrial-laser-distance-sensor/69027975.html) |
| ETYS-50X-2 | 1535 nm | 5000 m | ±2m (±1m customizable) | Up to 5 Hz | RS422-TTL | 85.0 g |  | [page](https://www.jrt-measure.com/micro-laser-distance-sensor/57289478.html) |
| ETYS-10KX-1 | 1535 nm | 10000 m | ±2m (optional ±1m) | single shot, 1Hz, 5Hz | RS422 | 230.0 g |  | [page](https://www.jrt-measure.com/long-range-distance-sensor/68385464.html) |
| ETYS2-12KX-1 | 1535 nm | 12000 m | <=±2m | Single shot, 1–5Hz, 10Hz |  | 230.0 g |  | [page](https://www.jrt-measure.com/new-arrivals-laser-rangefinder-module/69012562.html) |

### Lumispot Tech

| Model | Wavelength | Max range | Accuracy | Rate | Interface | Weight | Public price | Source |
|---|---|---|---|---|---|---|---|---|
| DLRF-C1 1.2KM High Repetition Module | 905 nm | 1200 m | ±0.5m (<=80m); ±1m (>80m) | 60~800Hz (self-adaption) | UART (TTL_3.3V) | 11.0 g |  | [page](https://www.lumispot-tech.com/1-2km-high-repetition-laser-rangefinder-module-product/) |
| DLRF-C1 1.5KM Module | 905 nm | 1500 m | ±0.5m (<=80m); ±1m (<=1000m); ±(0.2+0.0015*D) (>1000m) | 1~10Hz (self-adaption) | UART (TTL_3.3V) | 11.0 g |  | [page](https://www.lumispot-tech.com/1-5km-laser-rangefinder-module-product/) |
| DLRF-C2 2KM Module | 905 nm | 2000 m | ±0.5m (<=80m); ±1m (<=1000m); ±(0.2+0.0015*D) (>1000m) | 1~10Hz (self-adaption) | UART (TTL_3.3V) | 11.0 g |  | [page](https://www.lumispot-tech.com/2km-laser-rangefinder-module-3-product/) |
| ELRF-C16 (Micro 3KM class) | 1535 nm | 5000 m | <=±1m | 1~10Hz | RS422 serial, CAN (TTL optional) | 33.0 g |  | [page](https://www.lumispot-tech.com/micro-3km-laser-rangefinder-module-product/) |

### DFRobot

| Model | Wavelength | Max range | Accuracy | Rate | Interface | Weight | Public price | Source |
|---|---|---|---|---|---|---|---|---|
| SEN0259 TFmini LiDAR (ToF) Laser Range Sensor (12m) | 850 nm | 12 m | 1% (<6m), 2% (6 ~ 12m) | 100Hz | UART (TTL) | 4.7 g |  | [page](https://wiki.dfrobot.com/SEN0259) |
| TFmini Plus (listed on DFRobot SEN0259 wiki page) | 850 nm | 12 m | ±5 cm (0.1–6 m); ±1% (6–12 m) | 1–1000 Hz (adjustable) | UART, I²C, I/O | 12 g |  | [page](https://wiki.dfrobot.com/SEN0259) |

## Contributing

Add a row to `data/modules.json`, run `python scripts/validate.py`, and link the manufacturer page you copied from in the PR. Only values the manufacturer publishes; no reseller pages, no forum numbers.

## Related

- [awesome-laser-rangefinder](https://github.com/Tommyapi/awesome-laser-rangefinder) — curated links: manufacturers, drivers, flight-controller integration, guides
- [lrf-uart-protocol-decoder](https://github.com/Tommyapi/lrf-uart-protocol-decoder) — decode UART frames from several of these modules in the browser or Python
- [drone-altimeter-laser-rangefinder-guide](https://github.com/Tommyapi/drone-altimeter-laser-rangefinder-guide) — choosing and mounting a laser altimeter on a UAV

## Support / 打赏

If this project saved you time, you can buy the author a coffee in crypto. Thank you!
如果这个项目帮到了你，欢迎用加密货币打赏支持，谢谢！

| Network | Asset | Address |
|---|---|---|
| TRON (TRC20) | USDT | `TNGdTwE6opH6rmUyoG1JUR7FSyEb4k273R` |
| Ethereum / BNB Chain / Polygon | USDT | `0x59c43144a862b351fa1086ae842d1327c9d91613` |
| Ethereum / Arbitrum / Base | ETH | `0x59c43144a862b351fa1086ae842d1327c9d91613` |
| Bitcoin | BTC | `1RS6tWXHregLfEsiPzVUCUBuhgDg5uTSV` |
| Solana | USDT | `HZguEXfTtLChNdJTxAYCbcGscaqikz8JYrEpUhEyeVd9` |

Please send only the listed asset on the listed network — other tokens or networks may be lost.
请按表中对应的网络转对应的币种，转错币种或网络可能无法找回。

Built by tommyapi.com

## License

MIT — see [LICENSE](LICENSE). Spec values remain the property of their manufacturers; this repository only collects published figures with their source.
