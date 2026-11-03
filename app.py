from flask import Flask, render_template, request, jsonify, send_file
from Crypto.Cipher import DES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
from datetime import datetime, timezone
import base64
import csv
import io
import time
import webbrowser
from threading import Timer

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024

RESULTS = []


# Educational demonstration only.
# DES is obsolete and must not be used to protect real information.
# The brute-force experiment searches only a bounded test-key space.


def key_from_number(n):
    return int(n).to_bytes(8, 'big')


def b64e(b):
    return base64.b64encode(b).decode('ascii')


def b64d(s):
    return base64.b64decode(s, validate=True)


@app.get('/')
def index():
    return render_template('index.html')


@app.post('/api/encrypt')
def encrypt():
    data = request.get_json(force=True)
    message = str(data.get('message', ''))
    key_hex = str(data.get('key_hex', '')).strip()

    if not message or len(message) > 4000:
        return jsonify(
            error='Enter a message of 1–4000 characters.'
        ), 400

    try:
        key = bytes.fromhex(key_hex) if key_hex else get_random_bytes(8)
    except ValueError:
        return jsonify(error='Key must be hexadecimal.'), 400

    if len(key) != 8:
        return jsonify(
            error='DES requires an 8-byte (16 hexadecimal character) key.'
        ), 400

    iv = get_random_bytes(8)
    cipher = DES.new(key, DES.MODE_CBC, iv=iv)
    ciphertext = cipher.encrypt(
        pad(message.encode('utf-8'), DES.block_size)
    )

    return jsonify(
        key_hex=key.hex(),
        iv_b64=b64e(iv),
        ciphertext_b64=b64e(ciphertext),
        note=(
            'Educational demonstration only. DES is obsolete '
            'and unsuitable for real data.'
        )
    )


@app.post('/api/decrypt')
def decrypt():
    data = request.get_json(force=True)

    try:
        key = bytes.fromhex(
            str(data.get('key_hex', '')).strip()
        )
        iv = b64d(
            str(data.get('iv_b64', '')).strip()
        )
        ciphertext = b64d(
            str(data.get('ciphertext_b64', '')).strip()
        )

        if (
            len(key) != 8
            or len(iv) != 8
            or not ciphertext
            or len(ciphertext) % 8 != 0
        ):
            raise ValueError(
                'Invalid DES key, IV, or ciphertext length.'
            )

        cipher = DES.new(key, DES.MODE_CBC, iv=iv)
        decrypted = cipher.decrypt(ciphertext)
        plaintext = unpad(decrypted, DES.block_size)

        return jsonify(plaintext=plaintext.decode('utf-8'))

    except Exception:
        return jsonify(
            error=(
                'Decryption failed. Check the key, IV, '
                'ciphertext, and padding.'
            )
        ), 400


@app.post('/api/experiment')
def experiment():
    data = request.get_json(force=True)

    try:
        target = int(data.get('target', 37))
        space = int(data.get('space', 256))
    except (TypeError, ValueError):
        return jsonify(
            error='Target and key-space size must be integers.'
        ), 400

    if not 2 <= space <= 4096 or not 0 <= target < space:
        return jsonify(
            error='Use a key space of 2–4096 and a target inside that space.'
        ), 400

    known = b'DESLab demo'
    target_key = key_from_number(target)
    iv = bytes.fromhex('0102030405060708')

    ciphertext = DES.new(
        target_key, DES.MODE_CBC, iv=iv
    ).encrypt(pad(known, DES.block_size))

    start = time.perf_counter()
    attempts = 0
    found = None

    for candidate in range(space):
        attempts += 1

        try:
            trial_cipher = DES.new(
                key_from_number(candidate),
                DES.MODE_CBC,
                iv=iv
            )
            trial = unpad(
                trial_cipher.decrypt(ciphertext),
                DES.block_size
            )

            if trial == known:
                found = candidate
                break

        except ValueError:
            pass

    elapsed = time.perf_counter() - start
    rate = attempts / elapsed if elapsed > 0 else None

    row = {
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'key_space': space,
        'target_index': target,
        'found_index': found,
        'attempts': attempts,
        'elapsed_seconds': round(elapsed, 8),
        'attempts_per_second': round(rate, 2) if rate else None,
        'success': found == target,
        'scope': 'bounded app-generated test ciphertext'
    }

    RESULTS.append(row)

    return jsonify({
        **row,
        'total_runs': len(RESULTS)
    })


@app.get('/api/results')
def results():
    return jsonify(RESULTS)


@app.get('/api/results.csv')
def results_csv():
    output = io.StringIO()

    fields = [
        'timestamp_utc',
        'key_space',
        'target_index',
        'found_index',
        'attempts',
        'elapsed_seconds',
        'attempts_per_second',
        'success',
        'scope'
    ]

    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    writer.writerows(RESULTS)

    raw = io.BytesIO(output.getvalue().encode('utf-8'))
    raw.seek(0)

    return send_file(
        raw,
        mimetype='text/csv',
        as_attachment=True,
        download_name='deslab_experiment_results.csv'
    )


@app.get('/api/estimate')
def estimate():
    try:
        rate = float(request.args.get('rate', '10000'))
    except ValueError:
        rate = 10000

    if not 0 < rate <= 1e12:
        return jsonify(
            error='Rate must be between 1 and 1e12 attempts/second.'
        ), 400

    bits = [8, 12, 16, 20, 24, 28, 32, 40, 48, 56]
    rows = []

    for b in bits:
        keys = 2 ** b
        avg_seconds = (keys / 2) / rate

        rows.append({
            'bits': b,
            'key_count': keys,
            'average_seconds': avg_seconds,
            'worst_seconds': keys / rate
        })

    return jsonify(
        rate=rate,
        rows=rows,
        note=(
            'Theoretical extrapolation only; not a measured full-DES attack. '
            'DES effective key length is 56 bits.'
        )
    )


if __name__ == '__main__':
    # Open the browser automatically when starting the local website.
    Timer(
        1.0,
        lambda: webbrowser.open('http://127.0.0.1:5000')
    ).start()

    # Local development only.
    # Disable the reloader to avoid duplicate browser tabs.
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True,
        use_reloader=False
    )