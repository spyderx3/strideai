import numpy as np

# Signal processing functions; makes readings smoother
def smooth_signal(values, window_size=5):

    if len(values) < window_size:
        return values

    smoothed = []

    half_window = window_size // 2

    for i in range(len(values)):

        start = max(0, i - half_window)
        end = min(len(values), i + half_window + 1)

        window = values[start:end]

        smoothed.append(
            sum(window) / len(window)
        )

    return smoothed

# ===========================
# Calculating general sprint features
# ===========================

# Calculates stride length for speed (Speed = Stride Length * Cadence)
def calculate_stride_length(
    left_ankle_x,
    right_ankle_x,
    left_hip_x,
    right_hip_x
):

    stride_values = []

    for i in range(len(left_ankle_x)):

        hip_width = abs(
            left_hip_x[i] -
            right_hip_x[i]
        )

        # Ignore small hip widths
        if hip_width < 0.01:
            continue

        ankle_distance = abs(
            left_ankle_x[i] -
            right_ankle_x[i]
        )

        stride_ratio = ankle_distance / hip_width

        # Ignore VERY unrealistic stride ratios
        if stride_ratio < 6:
            stride_values.append(stride_ratio)  

    if not stride_values:
        return 0

    print(
        "Stride samples:",
        len(stride_values),
        "Min:",
        min(stride_values) if stride_values else None,
        "Max:",
        max(stride_values) if stride_values else None
    )
    return np.percentile(stride_values, 90)

# Calculates cadence for stride mechanics
def calculate_cadence(left_knee, right_knee, duration_seconds):

    peak_count = 0

    for signal in [left_knee, right_knee]:

        last_peak = -100
        threshold = np.mean(signal)

        for i in range(1, len(signal)-1):

            if (
                signal[i] > signal[i-1]
                and signal[i] > signal[i+1]
                and signal[i] > threshold
                and (i-last_peak) > 4
            ):
                peak_count += 1
                last_peak = i

    if duration_seconds <= 0:
        return 0

    return (peak_count / duration_seconds) * 60

# Estimates ground contact time for stride mechanics
def estimate_ground_contact(ankle_y, fps):

    velocity = []

    for i in range(1, len(ankle_y)):
        velocity.append(
            abs(ankle_y[i] - ankle_y[i-1])
        )

    if not velocity:
        return 0

    # smooth velocity
    velocity = smooth_signal(velocity)

    threshold = np.percentile(velocity, 35)

    contact_frames = []
    current = 0

    for v in velocity:

        if v < threshold:
            current += 1

        else:
            if current > 0:
                contact_frames.append(current)
            current = 0

    if current > 0:
        contact_frames.append(current)

    if not contact_frames:
        return 0

    return (
        sum(contact_frames) / len(contact_frames)
    ) / fps

# ===========================
# Performance scoring
# ===========================

# Calculates a score based on cadence
def cadence_score(cadence):

    if cadence >= 260:
        return 100

    elif cadence >= 240:
        return 90

    elif cadence >= 220:
        return 80

    elif cadence >= 200:
        return 70

    return 60

# Calculates a score based on stride symmetry
def symmetry_score(diff):

    if diff <= 5:
        return 100

    elif diff <= 10:
        return 85

    elif diff <= 15:
        return 70

    return 50

# Calculates a score based on trunk lean
def trunk_score(lean):

    if 5 <= lean <= 15:
        return 100

    elif 3 <= lean <= 20:
        return 90

    elif 0 <= lean <= 25:
        return 75

    return 60

# Calculates a score based on knee velocity
def velocity_score(peak_velocity):

    if peak_velocity >= 450:
        return 100

    elif peak_velocity >= 400:
        return 90

    elif peak_velocity >= 300:
        return 80

    elif peak_velocity >= 200:
        return 70

    return 60

# MAIN FUNCTION: Analyzes sprint performance metrics
def analyze_sprint(frame_metrics):

    if not frame_metrics:
        return {
            "summary": {},
            "performance": {},
            "coaching": {},
            "score": None,
        }
    
    duration_seconds = (
        frame_metrics[-1]["time"] -
        frame_metrics[0]["time"]
    ) / 1000

    # 1. Collect raw knee angles
    left_knee = [
        frame["left_knee"]
        for frame in frame_metrics
    ]

    right_knee = [
        frame["right_knee"]
        for frame in frame_metrics
    ]

    left_knee = smooth_signal(left_knee)
    right_knee = smooth_signal(right_knee)

    # Collect and smooth trunk lean angles
    trunk = [
        frame["trunk_lean"]
        for frame in frame_metrics
    ]

    trunk = smooth_signal(trunk)

    avg_trunk = sum(trunk) / len(trunk)
    max_trunk = max(trunk)
    min_trunk = min(trunk)

    # Collect and smooth ankle positions 
    left_ankle = [
        frame["left_ankle_y"]
        for frame in frame_metrics
    ]

    left_ankle_x = [
    frame["left_ankle_x"]
    for frame in frame_metrics
    ]

    right_ankle_x = [
        frame["right_ankle_x"]
        for frame in frame_metrics
    ]

    left_hip_x = [
        frame["left_hip_x"]
        for frame in frame_metrics
    ]

    right_hip_x = [
        frame["right_hip_x"]
        for frame in frame_metrics
    ]

    right_ankle = [
        frame["right_ankle_y"]
        for frame in frame_metrics
    ]

    left_ankle = smooth_signal(left_ankle)
    right_ankle = smooth_signal(right_ankle)
    
    print(min(left_knee))
    print(max(left_knee))


    for i in range(len(frame_metrics)):
        frame_metrics[i]["left_knee"] = left_knee[i]
        frame_metrics[i]["right_knee"] = right_knee[i]

    cadence = calculate_cadence(
        left_knee,
        right_knee,
        duration_seconds
    )

    stride_length = calculate_stride_length(
        left_ankle_x,
        right_ankle_x,
        left_hip_x,
        right_hip_x
    )
        
    # 3. Calculate knee angular velocity
    left_knee_velocity = []
    right_knee_velocity = []

    for i in range(1, len(frame_metrics)):

        previous = frame_metrics[i-1]
        current = frame_metrics[i]

        time_difference = (
            current["time"] - previous["time"]
        ) / 1000  # milliseconds → seconds

        if time_difference > 0:

            left_change = abs(
                current["left_knee"] -
                previous["left_knee"]
            )

            right_change = abs(
                current["right_knee"] -
                previous["right_knee"]
            )

            if left_change > 50 or right_change > 50:
                continue

            left_velocity = (
                current["left_knee"] - previous["left_knee"]
            ) / time_difference

            right_velocity = (
                current["right_knee"] - previous["right_knee"]
            ) / time_difference

            left_knee_velocity.append(abs(left_velocity))
            right_knee_velocity.append(abs(right_velocity))

    # 4. Calculate average velocities
    if left_knee_velocity and right_knee_velocity:
        avg_knee_velocity = (
            sum(left_knee_velocity) +
            sum(right_knee_velocity)
        ) / (
            len(left_knee_velocity) +
            len(right_knee_velocity)
        )
    else:
        avg_knee_velocity = 0

    # 5. Calculate maximum velocities
    if left_knee_velocity and right_knee_velocity:
        all_velocities = left_knee_velocity + right_knee_velocity
        all_velocities.sort()
        index = int(0.95 * len(all_velocities))
        peak_knee_velocity = all_velocities[index]
    else:
        peak_knee_velocity = 0

    # Test print
    print(
        f"Avg Velocity: {avg_knee_velocity:.1f}"
    )
    print(
        f"Peak Velocity: {peak_knee_velocity:.1f}"
    )
    print(
        f"Cadence: {cadence:.1f}"
    )
    print(
        f"Stride Length: {stride_length:.2f}x hip width"
    )
    
    # 6. Classify movement intensity
    if (
        peak_knee_velocity > 400
        and avg_knee_velocity > 100
    ):
        movement_type = "Sprint"

    elif avg_knee_velocity > 60:
        movement_type = "Jogging"

    else:
        movement_type = "Walking"

    # 7. Calculate average knee positions
    left_avg = sum(left_knee) / len(left_knee)
    right_avg = sum(right_knee) / len(right_knee)

    left_min = min(left_knee)
    right_min = min(right_knee)

    left_max = max(left_knee)
    right_max = max(right_knee)

    # 8. Collect average hip positions
    left_hip = [
        frame["left_hip"]
        for frame in frame_metrics
    ]

    right_hip = [
        frame["right_hip"]
        for frame in frame_metrics
    ]

    # 9. Calculate average hip positions
    left_hip_avg = sum(left_hip) / len(left_hip)
    right_hip_avg = sum(right_hip) / len(right_hip)

    left_hip_min = min(left_hip)
    right_hip_min = min(right_hip)

    left_hip_max = max(left_hip)
    right_hip_max = max(right_hip)

    # 10. Calculate knee symmetry difference
    knee_symmetry_difference = abs(left_avg - right_avg)

    # 11. Calculate feedback

    coaching = {
        "summary": "",
        "strengths": [],
        "focus_areas": [],
        "drills": []
    }

    if movement_type != "Sprint":

        coaching["focus_areas"].append(
            "Upload a sprint or acceleration video for a complete biomechanics analysis."
        )

        coaching["strengths"].append(
            f"Peak knee velocity: {peak_knee_velocity:.1f}°/sec"
        )

        coaching["strengths"].append(
            f"Average knee velocity: {avg_knee_velocity:.1f}°/sec"
        )

        return {

            "summary": {

                "left_knee": {
                    "average": left_avg,
                    "minimum": left_min,
                    "maximum": left_max
                },

                "right_knee": {
                    "average": right_avg,
                    "minimum": right_min,
                    "maximum": right_max
                },

                "left_hip": {
                    "average": left_hip_avg,
                    "minimum": left_hip_min,
                    "maximum": left_hip_max
                },

                "right_hip": {
                    "average": right_hip_avg,
                    "minimum": right_hip_min,
                    "maximum": right_hip_max
                },

                "trunk_lean": {
                    "average": avg_trunk,
                    "minimum": min_trunk,
                    "maximum": max_trunk
                },
            },

                "performance": {
                    "knee_symmetry_difference": knee_symmetry_difference,
                    "movement_type": movement_type,
                    "average_knee_velocity": avg_knee_velocity,
                    "peak_knee_velocity": peak_knee_velocity,
                    "cadence": cadence,
                    "average_trunk_lean": avg_trunk,
                    "stride_length": stride_length
                },
                
                "coaching": coaching,

                "score": None
            }

    # 12. Generate coaching recommendations

    # Knee symmetry score (0–100)
    if knee_symmetry_difference <= 5:
        symmetry_score = 100
    elif knee_symmetry_difference <= 10:
        symmetry_score = 80
    elif knee_symmetry_difference <= 15:
        symmetry_score = 60
    else:
        symmetry_score = 40

    # Trunk lean score (0–100)
    if 5 <= avg_trunk <= 15:
        trunk_score = 100
    elif avg_trunk <= 20:
        trunk_score = 80
    elif avg_trunk <= 30:
        trunk_score = 60
    elif avg_trunk <= 40:
        trunk_score = 40
    else:
        trunk_score = 20

    # Cadence score (0–100)
    if 240 <= cadence <= 300:
        cadence_score = 100
    elif 220 <= cadence <= 320:
        cadence_score = 80
    elif 180 <= cadence <= 340:
        cadence_score = 60
    else:
        cadence_score = 40

    # Stride length score (0–100)
    if 3.0 <= stride_length <= 4.5:
        stride_score = 100
    elif 2.5 <= stride_length <= 5.0:
        stride_score = 80
    elif 2.0 <= stride_length <= 5.5:
        stride_score = 60
    else:
        stride_score = 40

    # Velocity score (0–100)
    if peak_knee_velocity >= 500:
        velocity_score = 100
    elif peak_knee_velocity >= 350:
        velocity_score = 80
    elif peak_knee_velocity >= 200:
        velocity_score = 60
    else:
        velocity_score = 40

    overall_score = (
        symmetry_score * 0.25 +
        trunk_score * 0.30 +
        cadence_score * 0.20 +
        stride_score * 0.15 +
        velocity_score * 0.10
    )

    score = round(overall_score)

    # Test scores
    print(f"Symmetry Score: {symmetry_score}")
    print(f"Trunk Score: {trunk_score}")
    print(f"Cadence Score: {cadence_score}")
    print(f"Stride Score: {stride_score}")
    print(f"Velocity Score: {velocity_score}")
    print(f"Overall Score: {score}")

    # Trunk coaching
    if avg_trunk < 5:
            coaching["focus_areas"].append(
                "Increase forward lean slightly during acceleration."
            )

    elif avg_trunk <= 15:
            coaching["strengths"].append(
                "Stable trunk posture throughout the sprint."
            )

    elif avg_trunk <= 25:
            coaching["focus_areas"].append(
                "Maintain optimal trunk lean as speed increases."
            )

    else:
            coaching["focus_areas"].append(
                "Reduce excessive forward lean to improve efficiency and lower injury risk."
            )

    # Knee symmetry feedback
    if knee_symmetry_difference <= 5:
        coaching["strengths"].append(
            "Excellent left/right knee symmetry."
        )

    elif knee_symmetry_difference <= 10:
        coaching["focus_areas"].append(
            "Improve left/right knee symmetry for better force production."
        )

    else:
        coaching["focus_areas"].append(
            "Address noticeable left/right asymmetry during ground contact."
        )

    # Stride length feedback
    if 3.0 <= stride_length <= 4.5:

        coaching["strengths"].append(
            "Good stride length relative to hip width."
        )

    else:

        coaching["focus_areas"].append(
            "Improve stride length consistency."
        )

    # Cadence feedback
    if 240 <= cadence <= 300:

        coaching["strengths"].append(
            "Efficient sprint cadence."
        )

    else:

        coaching["focus_areas"].append(
            "Optimize stride turnover for better sprint efficiency."
        )

    # Drill recommendations
    if avg_trunk > 25:

        coaching["drills"].append(
            "Wall acceleration drills"
        )

    if knee_symmetry_difference > 10:

        coaching["drills"].append(
            "Single-leg bounds"
        )

    if cadence < 220:

        coaching["drills"].append(
            "Fast-feet cadence drills"
        )

    if score >= 90:

        coaching["summary"] = (
            "Excellent sprint mechanics with only minor areas for refinement."
        )

    elif score >= 80:

        coaching["summary"] = (
            "Strong sprint mechanics with a few opportunities for improvement."
        )

    elif score >= 70:

        coaching["summary"] = (
            "Solid sprint mechanics, but several technical improvements could increase efficiency."
        )

    else:

        coaching["summary"] = (
            "Sprint mechanics show multiple areas that would benefit from focused technique work."
        )

    # 13. Return results of analysis
    return {

        "summary": {

            "left_knee": {
                "average": left_avg,
                "minimum": left_min,
                "maximum": left_max
            },

            "right_knee": {
                "average": right_avg,
                "minimum": right_min,
                "maximum": right_max
            },

            "left_hip": {
                "average": left_hip_avg,
                "minimum": left_hip_min,
                "maximum": left_hip_max
            },

            "right_hip": {
                "average": right_hip_avg,
                "minimum": right_hip_min,
                "maximum": right_hip_max    
            },

            "trunk_lean": {
                "average": avg_trunk,
                "minimum": min_trunk,
                "maximum": max_trunk
            }
        },

        "performance": {
            "knee_symmetry_difference": knee_symmetry_difference,
            "movement_type": movement_type,
            "average_knee_velocity": avg_knee_velocity,
            "peak_knee_velocity": peak_knee_velocity,
            "cadence": cadence,
            "average_trunk_lean": avg_trunk,
            "stride_length": stride_length
        },

        "coaching": coaching,

        "score": score 
    }