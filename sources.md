# Sustainability Data Sources

All values are point estimates synthesized from the citations below. Where 
component-level data isn't publicly available, system-level LCAs were 
decomposed using established contribution percentages (e.g., NVIDIA's H100 PCF 
disclosing memory at 42%, ICs at 25%, thermal components at 18%).

## Primary Sources

### Manufacturer Product Carbon Footprints (PCFs)

**[dell_r740_lca_2019]** Dell Technologies, "Life Cycle Assessment of Dell 
PowerEdge R740," 2019. https://corporate.delltechnologies.com/content/dam/digitalassets/active/en/unauth/data-sheets/products/servers/lca_poweredge_r740.pdf
- Used for: motherboard, RAM embodied CO2 decomposition.
- Methodology: PAIA model (MIT Materials Systems Lab).

**[dell_r360_pcf_2023]** Dell Technologies, "Product Carbon Footprint PowerEdge R360," 
2023. Mean: 1,140 ± 943 kgCO2e. 
https://www.delltechnologies.com/asset/en-us/products/servers/technical-support/poweredge-r360-pcf-datasheet.pdf
- Used for: server chassis baseline embodied CO2.

**[dell_r750_pcf_2022]** Dell Technologies, "Product Carbon Footprint PowerEdge 
R750," 2022. Mean: 5,870 ± 2,830 kgCO2e. 
https://www.delltechnologies.com/asset/en-us/products/servers/technical-support/poweredge-r750.pdf
- Used for: high-end server reference, chassis cross-check.

**[nvidia_h100_pcf_2024]** NVIDIA, "Product Carbon Footprint for H100 baseboard 
(8x H100 SXM)." Total: 1,312 kgCO2e cradle-to-gate; ~164 kgCO2e per card. 
Memory 42%, ICs 25%, thermal components 18%.
Referenced in: arxiv.org/html/2509.00093v1 (Sept 2025) and 
interactdc.com/posts/understanding-gpus-energy-and-environmental-impact-part-i/
- Used for: GPU embodied CO2.

**[seagate_decarbonizing_data_2025]** Seagate Technology, "Decarbonizing Data 
Report," April 2025. https://www.seagate.com/resources/decarbonizing-data-report/
- 30TB Mozaic HDD: 29.7 kgCO2e embodied
- 30.72TB SSD (estimated): 4,915 kgCO2e embodied
- HDD operational: 9.6W; SSD operational: 20W
- Per-TB-per-year: <0.2 kg CO2/TB/yr (HDD) vs ~32 kg (SSD)
- ⚠ DISPUTED: Pure Storage, Solidigm, and Ocient published rebuttals in 
  June 2025 arguing the SSD figure is overstated by 4x; they place the gap at 
  <2x rather than 8x. Both sides cited in Q&A prep.

### Authoritative Aggregators

**[ewaste_monitor_2024]** Baldé, C.P., et al. "The Global E-waste Monitor 2024." 
ITU and UNITAR, March 2024. https://ewastemonitor.info/the-global-e-waste-monitor-2024/
Key figures used:
- 62 million tonnes global e-waste in 2022 (up 82% since 2010)
- $91B total embedded metal value, only $28B recovered
- $19B copper, $15B gold, $16B iron in annual e-waste stream
- 22.3% formal recycling rate (US/global); 42.8% in Europe
- 93 million tonnes CO2-equivalent emissions avoided through formal recycling
- 17.6 kg per capita generation in high-income countries
- Used for: undetected fallback, all "money shot" pitch numbers

**[usgs_rare_earths_hdd_2024]** USGS Mineral Commodity Summaries 2024 — 
Rare Earth Elements section. https://pubs.usgs.gov/periodicals/mcs2024/
- Neodymium content in HDD voice coil and spindle motors: ~10-20g per 3.5" 
  enterprise drive
- Used for: HDD recoverable materials.

### Industry / Research

**[scarif_2024_estimate]** Ji, S. et al., "SCARIF: Towards Carbon Modeling of 
Cloud Servers with Accelerators," arxiv.org/pdf/2401.06270, 2024.
- Provides component-level breakdown of server embodied carbon, including CPUs, 
  accelerators, and NICs.
- Used for: CPU and network card embodied CO2 estimates.

**[seagate_dirty_secret_ssd_2022]** "The Dirty Secret of SSDs: Embodied Carbon," 
HotCarbon Workshop, 2022. arxiv.org/pdf/2207.10793
- SEF: 0.16 kgCO2e per GB for SSDs (industry-disputed).

**[pcb_recovery_avg_2024]** Synthesis of:
- Aivon PCB Knowledge, 2025: 300-500g copper per kg of PCB; 0.03-0.1% gold in 
  finger contacts. https://www.aivon.com/blog/pcb-knowledge/diy-pcb-recycling-safely-recovering-metals-from-old-circuit-boards/
- Yamane et al., "Characterization of PCBs for Metal and Energy Recovery," 
  PMC5455934 (~26% metal by mass)
- PCBMaster, 2025: 100-300g gold per ton of high-grade PCB scrap
- Mt Baker Mining: 3-8 oz gold/ton, 15-20 oz silver/ton, 500+ lbs copper/ton
- Used for: per-component precious metal estimates (motherboard, GPU, RAM, etc.)

**[scrapcatalogue_psu_2025]** "PC Power Supply Scrap," ScrapCatalogue, May 2025. 
https://www.scrapcatalogue.com/pc-power-supply-scrap/
- PSU material breakdown: copper transformers/wires, aluminum heatsinks, 
  steel casing, low precious metals
- Hazard: high-voltage capacitors

**[scrapmonster_cable_2024]** ScrapMonster Power Supplies/Cable scrap pricing 
guide. https://www.scrapmonster.com/scrap/power-supplies/73
- Used for: cable copper content and scrap value.

**[alta_technologies_2025]** Alta Technologies enterprise IT resale catalog. 
https://altatechnologies.com/
- Used for: refurb price ranges (GPU, NIC, PSU).

**[pcsp_2026]** PC Server & Parts (PCSP) refurbished server pricing, 2026. 
https://pcserverandparts.com/
- Examples: Dell PowerEdge R740XD from $629.99; R640 from $214.99; 
  HPE ProLiant DL380 Gen10 from $199.98
- Used for: refurb price ranges (CPU, RAM, motherboard, SSD, HDD, chassis).

## Methodology Notes

1. **Component-level estimates**: When component-specific PCFs aren't 
   published (most cases), system-level LCAs were decomposed using NVIDIA H100's 
   public breakdown (memory 42%, ICs 25%, thermal 18%) and SCARIF model 
   weights as a sanity check.

2. **Refurb ranges**: Wide ranges reflect that an enterprise GPU like an H100 
   sells for $15k+ used, while a consumer GTX 1060 sells for ~$50. The decision 
   layer should treat the range, not a midpoint, as the signal.

3. **Recoverable value (USD)**: Calculated from listed metal masses at 
   commodity prices as of late 2025 (Cu ~$9.50/kg, Au ~$95/g, Ag ~$1/g). 
   These values represent *theoretical scrap value*, not what an individual 
   would receive — recyclers retain margin.

4. **Conservative bias**: Where sources disagreed, the lower of the credible 
   range was chosen (e.g., SSD CO2 used 5 kg/TB rather than Seagate's higher 
   figure, in line with the Pure/Solidigm rebuttal).

5. **The "undetected" category**: deliberately conservative — assumes e-waste 
   pathway and never recommends landfill. Per-kg CO2 derived from the UN 
   E-Waste Monitor's $91B / 62 Mt aggregate ÷ avg item mass.

## Price Range Derivation

USD fields in `sustainability_data.json` (`scrap_value_usd`, 
`refurb_value_modern_usd`, `refurb_value_legacy_usd`) are stored as 
`[low, high]` arrays rather than point estimates. This is because the 
underlying spread is the signal — a midpoint would hide it. The general 
rules:

- **`scrap_value_usd` high end** = theoretical max value computed directly 
  from the component's `recoverable_metals_g` at late-2025 commodity prices 
  (Cu ~$9.50/kg, Au ~$95/g, Ag ~$1/g; Al ~$2.50/kg, steel ~$0.40/kg, 
  Pd ~$35/g, Pt ~$30/g, Nd ~$0.10/g as oxide-equivalent).
- **`scrap_value_usd` low end** ≈ 30–40% of theoretical, reflecting the 
  margin recyclers retain before paying out to an individual seller (per 
  Methodology Note 3).
- **Refurb modern/legacy ranges** bracket what a working unit actually 
  trades for in current secondary markets, anchored to the source catalogs 
  (Alta, PCSP, scrap aggregators) rather than to any single SKU.

Per-component notes follow.

### gpu — `[scrap 4–12]`, `[modern 2000–15000]`, `[legacy 50–400]`

- Scrap: theoretical recoverable metal value is ~$11.40 (Au-dominated). 
  Range floor = ~35% recycler payout.
- Modern: bottom anchored at lower-tier modern accelerators (~$2k); top at 
  H100-class cards quoted at $15k+ used per Methodology Note 2.
- Legacy: bottom is the GTX 1060 reference (~$50, Methodology Note 2); top 
  covers older Tesla/Quadro datacenter cards still moving through 
  [alta_technologies_2025].

### cpu — `[scrap 6–19]`, `[modern 500–4000]`, `[legacy 15–100]`

- Scrap: gold-plated lid and pin grid push theoretical to ~$19. Floor at ~$6 
  is consistent with what scrap CPU buyers post per pound for modern LGA 
  parts.
- Modern: range covers the spread from a single Xeon Silver / EPYC 9004-low 
  ($500-ish) up to high-core EPYC / Xeon Platinum ($3-4k), per 
  [pcsp_2026] system-level pricing decomposed to CPU share.
- Legacy: Xeon E5 v3/v4 era pulls $15–100 depending on core count.

### psu — `[scrap 2–6]`, `[modern 80–400]`, `[legacy 10–60]`

- Scrap: theoretical ~$5.49, dominated by the copper transformer 
  ([scrapcatalogue_psu_2025]).
- Modern: redundant server PSUs (1100W–2400W Platinum/Titanium) sit at 
  $80–400 across [alta_technologies_2025].
- Legacy: older 750W/1100W units at $10–60.

### ram — `[scrap 1–5]`, `[modern 80–600]`, `[legacy 5–30]`

- Scrap: theoretical ~$4.88, almost entirely the gold edge connector.
- Modern: per-stick range covers DDR5 ECC RDIMM 32GB (~$80) up to 128GB 
  RDIMM (~$600) per [pcsp_2026].
- Legacy: DDR3/DDR4 ECC sticks at $5–30.

### motherboard — `[scrap 10–33]`, `[modern 300–1500]`, `[legacy 30–150]`

- Scrap: theoretical ~$32.85 — the highest of any single component on a 
  per-unit basis, driven by 0.25g Au + 0.1g Pd.
- Modern: server mainboards alone (no CPU/RAM) at $300–1500 per 
  [pcsp_2026].
- Legacy: R720/R730-era boards at $30–150.

### ssd — `[scrap 1–3]`, `[modern 400–2500]`, `[legacy 5–50]`

- Scrap: theoretical ~$3.05; flash itself has no recovery value, so the 
  range stays narrow.
- Modern: enterprise NVMe in the 7.68TB–30.72TB tier referenced by 
  [seagate_decarbonizing_data_2025] sells refurb at $400–2500.
- Legacy: SATA SSDs (240GB–960GB consumer/enterprise) at $5–50.

### hdd — `[scrap 3–10]`, `[modern 150–500]`, `[legacy 5–40]`

- Scrap: theoretical metal value alone is only ~$3.34, but recyclers price 
  whole drives higher because the neodymium magnet assembly is sold intact 
  (not refined) and the aluminum casting is a clean stream — hence the 
  $3–10 range rather than $1–3.
- Modern: 18TB–30TB enterprise drives (incl. Mozaic-class from 
  [seagate_decarbonizing_data_2025]) at $150–500 refurb.
- Legacy: 1–8TB enterprise SAS/SATA at $5–40.

### network_card — `[scrap 1–4]`, `[modern 200–2000]`, `[legacy 5–50]`

- Scrap: theoretical ~$4.17, gold-dominated.
- Modern: 100G/200G/400G Mellanox ConnectX-6/7 and Intel E810 NICs span 
  $200–2000 across [alta_technologies_2025].
- Legacy: 1G/10G NICs at $5–50.

### server_chassis — `[scrap 8–26]`, `[modern 200–1500]`, `[legacy 50–200]`

- Scrap: theoretical ~$26.25; steel is most of the mass but aluminum and 
  copper carry most of the value.
- Modern: directly anchored to [pcsp_2026] examples — DL380 Gen10 from 
  $199.98, R640 from $214.99, R740XD from $629.99 — extending up to $1500 
  for current-gen R760/DL380 Gen11.
- Legacy: pre-Gen10 / R720-era chassis at $50–200.

### power_network_cable — `[scrap 0.25–0.80]`, `[modern 3–25]`, `[legacy 0.50–2]`

- Scrap: bounded by copper content (theoretical ~$0.76 per 
  [scrapmonster_cable_2024]).
- Modern: covers the spread from a generic C13 power cable (~$3) to a DAC 
  or fiber breakout cable (~$25).
- Legacy: bulk used patch/power cables at $0.50–2.

### undetected

USD fields remain `null` — `default_action` is `manual_review`, and a 
numeric range would imply more confidence than is warranted.