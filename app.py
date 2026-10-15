from flask import Flask, request, jsonify
from hyundai_kia_connect_api import VehicleManager

app = Flask(__name__)
vm_cache = {}

@app.route('/ping', methods=['GET'])
def ping():
    return "pong", 200

@app.route('/get_soc', methods=['POST'])
def get_soc():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    pin = data.get('pin', '')

    if not username or not password:
        return jsonify({"error": "Missing credentials"}), 400

    try:
        cache_key = f"{username}"
        if cache_key in vm_cache:
            vm = vm_cache[cache_key]
        else:
            # Region 1 = Europe, Brand 1 = Kia
            vm = VehicleManager(
                region=1,
                brand=1,
                username=username,
                password=password,
                pin=pin
            )
            vm_cache[cache_key] = vm

        vm.check_and_refresh_token()
        vm.update_all_vehicles_with_cached_state()
        
        if not vm.vehicles:
            return jsonify({"error": "No vehicles found on this account"}), 404
            
        vehicle_id = list(vm.vehicles.keys())[0]
        vehicle = vm.vehicles[vehicle_id]
        
        return jsonify({
            "success": True,
            "soc": vehicle.ev_battery_percentage,
            "vehicle_name": vehicle.name,
            "last_updated": str(vehicle.last_updated_at)
        })
        
    except Exception as e:
        if username in vm_cache:
            del vm_cache[username]
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
