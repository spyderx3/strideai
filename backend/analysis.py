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

        if hip_width < 0.03:
            continue

        ankle_distance = abs(
            left_ankle_x[i] -
            right_ankle_x[i]
        )

        stride_ratio = ankle_distance / hip_width

        if stride_ratio < 5:
            stride_values.append(stride_ratio)  

    if not stride_values:
        return 0

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

# MAIN FUNCTION: Analyzes sprint performance metrics
def analyze_sprint(frame_metrics):

    if not frame_metrics:
        return {
            "summary": {},
            "performance": {},
            "score": None,
            "feedback": []
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

    # Estimate fps and calculate GCT
    fps = len(frame_metrics) / duration_seconds

    left_gct = estimate_ground_contact(
        left_ankle,
        fps
    )

    right_gct = estimate_ground_contact(
        right_ankle,
        fps
    )

    average_gct = (
        left_gct +
        right_gct
    ) / 2


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
    feedback = []

    if movement_type != "Sprint":

        feedback.append(
            f"Movement Detected: {movement_type} "
            f"(peak knee velocity: {peak_knee_velocity:.1f}°/sec)"
        )

        feedback.append(
            "This analysis is optimized for sprint mechanics. \nUpload a sprint or acceleration video to receive a biomechanics score."
        )

        feedback.append(
            f"Average knee velocity: {avg_knee_velocity:.1f}°/sec"
        )

        # Trunk lean feedback
        if avg_trunk < 5:
            feedback.append(
                "Running posture is very upright. A slight forward lean can improve acceleration."
            )

        elif avg_trunk <= 15:
            feedback.append(
                "Excellent trunk posture maintained during sprinting."
            )

        elif avg_trunk <= 25:
            feedback.append(
                "Moderate forward lean detected. Maintain posture as speed increases."
            )

        else:
            feedback.append(
                "Excessive forward lean may reduce efficiency and increase injury risk."
            )

        # Ground contact time feedback
        if average_gct < 0.12:

            feedback.append(
                "Excellent ground contact time. Force production is quick and efficient."
            )

        elif average_gct < 0.15:

            feedback.append(
                "Ground contact time is acceptable but could be shortened for greater speed."
            )

        else:

            feedback.append(
                "Ground contact time is relatively long. Focus on stiffness and quicker force application."
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
                    "average_trunk_lean": avg_trunk,
                    "ground_contact_time": average_gct,
                    "stride_length": stride_length
                },

                "feedback": feedback,

                "score": None
            }

    # 12. Calculate score
    if knee_symmetry_difference <= 5:
        score = 95
        feedback.append(
            "Excellent left/right knee symmetry throughout the run."
        )

    elif knee_symmetry_difference <= 10:
        score = 80
        feedback.append(
            f"Moderate knee asymmetry detected ({knee_symmetry_difference:.1f}° average difference)."
        )

    elif knee_symmetry_difference <= 15:
        score = 65
        feedback.append(
            f"Noticeable knee asymmetry detected ({knee_symmetry_difference:.1f}° average difference). Consider focusing on balanced mechanics."
        )

    else:
        score = 45
        feedback.append(
            f"Large knee asymmetry detected ({knee_symmetry_difference:.1f}° average difference). Recommend focusing on balancing left and right knee mechanics."
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
            "ground_contact_time": average_gct
        },

        "feedback": feedback,

        "score": score,  
    }