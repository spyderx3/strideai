def analyze_sprint(frame_metrics):

    if not frame_metrics:
        return {
            "summary": {},
            "performance": {},
            "score": None,
            "feedback": []
        }

    # Calculate average knee positions
    left_knee = [
        frame["left_knee"]
        for frame in frame_metrics
    ]

    right_knee = [
        frame["right_knee"]
        for frame in frame_metrics
    ]

    left_avg = sum(left_knee) / len(left_knee)
    right_avg = sum(right_knee) / len(right_knee)
    left_min = min(left_knee)
    right_min = min(right_knee)
    left_max = max(left_knee)
    right_max = max(right_knee)

    # Calculate average hip positions
    left_hip = [
        frame["left_hip"]
        for frame in frame_metrics
    ]

    right_hip = [
        frame["right_hip"]
        for frame in frame_metrics
    ]

    left_hip_avg = sum(left_hip) / len(left_hip)
    right_hip_avg = sum(right_hip) / len(right_hip)
    left_hip_min = min(left_hip)
    right_hip_min = min(right_hip)
    left_hip_max = max(left_hip)
    right_hip_max = max(right_hip)

    # Calculate knee symmetry difference
    knee_symmetry_difference = abs(left_avg - right_avg)

    # Calculate score and feedback
    feedback = []
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
            }

        },

        "performance": {
            "knee_symmetry_difference": knee_symmetry_difference
        },

        "feedback": feedback,

        "score": score,  
    }