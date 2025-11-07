from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, db, messaging
import time
import os

app = Flask(__name__)

# Initialize Firebase Admin SDK
try:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://accident-zone-dispatch-default-rtdb.asia-southeast1.firebasedatabase.app/'  # TODO: Replace!
    })
    print("✓ Firebase initialized")
except Exception as e:
    print(f"✗ Firebase init failed: {e}")


@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'service': 'Accident Zone Notification Server',
        'status': 'running'
    }), 200


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200


@app.route('/accident', methods=['POST'])
def report_accident():
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data'}), 400

        lat = float(data.get('latitude'))
        lng = float(data.get('longitude'))
        accident_id = f"accident_{int(time.time() * 1000)}"

        # Save to Firebase
        db.reference(f'accidents/{accident_id}').set({
            'latitude': lat,
            'longitude': lng,
            'status': 'active',
            'timestamp': int(time.time() * 1000),
            'source': 'esp8266'
        })
        print(f"✓ Saved: {accident_id}")

        # Send FCM
        message = messaging.Message(
            notification=messaging.Notification(
                title='🚨 Accident Detected!',
                body=f'New accident at {lat}, {lng}'
            ),
            data={'latitude': str(lat), 'longitude': str(lng), 'accidentId': accident_id},
            topic='accidents',
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(channel_id='accident_alerts')
            )
        )
        response = messaging.send(message)
        print(f"✓ FCM sent: {response}")

        return jsonify({'success': True, 'accidentId': accident_id}), 200
    except Exception as e:
        print(f"✗ Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n🚀 Server starting on port {port}...\n")
    app.run(host='0.0.0.0', port=port, debug=True)