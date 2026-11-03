# DESLab — Experimental Analysis of DES Strength and Brute-Force Attack

A local educational web application for BAD703 CCA. It demonstrates DES-CBC encryption/decryption, a **bounded brute-force search against an app-generated test ciphertext**, experiment logging, CSV export, and theoretical key-space estimates.

> **Safety and accuracy:** DES is obsolete and must not be used to protect real information. The search module is intentionally restricted to a user-selected key-index space of 2–4096. The 56-bit DES estimate is mathematical extrapolation, not a measured full-keyspace attack. This app is a classroom demonstration, not a production cryptography tool.

## Features
- Dark navy responsive dashboard.
- DES-CBC encrypt/decrypt for sample text.
- Bounded key search and measured attempts/time/rate.
- Theoretical key-space average/worst-case estimates.
- Experiment results table and CSV export.

## Requirements
- Python 3.10 or newer recommended
- pip
- Internet connection only for the optional CDN-hosted Chart.js and Google Fonts assets; backend runs locally.

## Run on Windows (PowerShell)
```powershell
cd path\to\DESLab
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```
Open `http://127.0.0.1:5000` in your browser. If PowerShell blocks activation, use `\.venv\Scripts\python.exe -m pip install -r requirements.txt` and `\.venv\Scripts\python.exe app.py`.

## Run on macOS/Linux
```bash
cd DESLab
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

## How to run a repeatable experiment
1. Open **Controlled Brute-Force Experiment**.
2. Choose a target index, e.g. `37`, and a key space, e.g. `256`.
3. Click **Run controlled search**.
4. Record attempts, elapsed seconds, and attempts/second. The target's position affects the number of attempts because the search checks candidates from zero upward.
5. Repeat with different target positions and spaces; export CSV.
6. Use measured outputs in your report. Do not substitute sample or invented values.

The small-index key mapping is only for making an observable classroom search practical. It is not representative of the entropy of the full 56-bit DES key space.

## API routes
- `GET /` — dashboard
- `POST /api/encrypt` — JSON `{ "message": "hello", "key_hex": "0123456789abcdef" }` (key may be omitted)
- `POST /api/decrypt` — JSON with `key_hex`, `iv_b64`, `ciphertext_b64`
- `POST /api/experiment` — JSON `{ "target": 37, "space": 256 }`
- `GET /api/results` — in-memory experiment results (cleared when server restarts)
- `GET /api/results.csv` — download experiment results
- `GET /api/estimate?rate=10000` — theoretical estimates

## Experimental analysis formulas
For key length `b`, key-space size is `N = 2^b`. At an assumed constant search rate `R` keys/second:
- Best case (ordered search, first candidate): approximately `1/R` seconds.
- Average case: approximately `N/(2R)` seconds.
- Worst case: approximately `N/R` seconds.

These estimates assume a constant rate and do not account for hardware, implementation, parallelism, key parity, or other attack-specific factors. Treat them as illustrative, not a forecast of a real attack.

## Suggested report structure
1. Abstract
2. Introduction and problem statement
3. Objectives and scope
4. DES theoretical background
5. System architecture and methodology
6. Implementation
7. Experimental design and measurements
8. Results and discussion (insert CSV-derived measurements and screenshots)
9. Limitations and ethical considerations
10. Conclusion
11. References

## GitHub upload
Create a repository named `DESLab-DES-Brute-Force-Analysis`, upload the project files, and add screenshots after running your own experiments. Do not commit private keys, real personal data, virtual environments, or claims/results you did not measure.

## References to consult
- NIST FIPS 46-3, *Data Encryption Standard (DES)* (withdrawn): https://csrc.nist.gov/pubs/fips/46-3/final
- NIST SP 800-67 Rev. 2, *Recommendation for the Triple Data Encryption Algorithm (TDEA)* (withdrawn): https://csrc.nist.gov/pubs/sp/800/67/r2/final
- NIST FIPS 197, *Advanced Encryption Standard (AES)*: https://csrc.nist.gov/pubs/fips/197/final
- PyCryptodome documentation: https://pycryptodome.readthedocs.io/
