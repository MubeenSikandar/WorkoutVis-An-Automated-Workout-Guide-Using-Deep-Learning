# PACKAGES

from helper_funcs import calculate_angle
import pickle
import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose


with open('repcounter.p', 'rb') as file:
    model = pickle.load(file)


# NOREP APP - MEDIAPIPE STREAM

cap = cv2.VideoCapture(0)

# Counter variables
counter = 0
grip = None
stance = None
stage = None

# Setup mediapipe instance

with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
    while cap.isOpened():
        ret, frame = cap.read()

        # Recolor image to RGB
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False

        # Make detection
        results = pose.process(image)

        # Recolor back to BGR
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # Extract landmarks
        try:
            landmarks = results.pose_landmarks.landmark

            # Get coordinates
            # Grip
            l_shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                          landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            r_shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,
                          landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
            l_elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                       landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
            r_elbow = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,
                       landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
            # Stance
            l_hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
                     landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
            r_hip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x,
                     landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
            l_ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                       landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
            r_ankle = [landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].x,
                       landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].y]

            # Calculate angles
            l_grip = calculate_angle(r_shoulder, l_shoulder, l_elbow)
            r_grip = calculate_angle(l_shoulder, r_shoulder, r_elbow)
            l_stance = calculate_angle(r_hip, l_hip, l_ankle)
            r_stance = calculate_angle(l_hip, r_hip, r_ankle)

            # Visualize angle  -  FOR DEBUGGING PURPOSES
            # cv2.putText(image, str(l_grip),
            #               tuple(np.multiply(l_shoulder, [640, 480]).astype(int)),
            #               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA
            #                    )
            # cv2.putText(image, str(r_grip),
            #               tuple(np.multiply(r_shoulder, [640, 480]).astype(int)),
            #               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA
            #                    )
            # cv2.putText(image, str(l_stance),
            #               tuple(np.multiply(l_ankle, [640, 480]).astype(int)),
            #               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2, cv2.LINE_AA
            #                    )
            # cv2.putText(image, str(r_stance),
            #               tuple(np.multiply(r_ankle, [640, 480]).astype(int)),
            #               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2, cv2.LINE_AA
            #                    )

            # Grip logic
            if (r_grip > 90) | (l_grip > 90) & (r_grip < 120) | (l_grip < 120):
                grip = 'Grip: Good!'
                posturebox = cv2.rectangle(
                    image, (0, 150), (225, 73), (200, 200, 16), -1)
            if (r_grip > 120) | (l_grip > 120):
                grip = 'Grip: Too wide'
                posturebox = cv2.rectangle(
                    image, (0, 150), (225, 73), (0, 145, 218), -1)
            if (r_grip < 90) | (l_grip < 90):
                grip = 'Grip: Too narrow'
                posturebox = cv2.rectangle(
                    image, (0, 150), (225, 73), (0, 145, 218), -1)

            # Stance logic
            if (r_stance > 88) | (l_stance > 88) & (r_stance < 98) | (l_stance < 98):
                stance = 'Stance: Good!'
                posturebox = cv2.rectangle(
                    image, (0, 150), (225, 73), (200, 200, 16), -1)
            if (r_stance > 98) | (l_stance > 98):
                stance = 'Stance: Too wide'
                posturebox = cv2.rectangle(
                    image, (0, 150), (225, 73), (0, 145, 218), -1)
            if (r_stance < 88) | (l_stance < 88):
                stance = 'Stance: Too narrow'
                posturebox = cv2.rectangle(
                    image, (0, 150), (225, 73), (0, 145, 218), -1)

            # Model implementation
            poses = results.pose_landmarks.landmark
            pose_row = np.array([[landmark.x, landmark.y, landmark.z]
                                for landmark in poses]).flatten()
            frame_height, frame_width = frame.shape[:2]
            pose_row = pose_row * \
                np.array([frame_width, frame_height, frame_width])[:, None]
            X = pd.DataFrame([pose_row[0]])
            body_language_class = model.predict(X)[0]
            body_language_prob = model.predict_proba(X)[0]

            # Rep counter logic
            if body_language_class == 0:
                stage = 'Down'
            if (body_language_class == 1) & (stage == 'Down'):
                stage = 'Up'
                counter += 1

        except:
            pass

        # Setup status box
        cv2.rectangle(image, (0, 0), (225, 73), (87, 122, 59), -1)
        postureboxlogic = posturebox
        postureboxlogic

        # Rep data
        cv2.putText(image, 'REPS', (25, 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
        cv2.putText(image, str(counter),
                    (30, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.3, (255, 255, 255), 2, cv2.LINE_AA)

        # Posture data
        cv2.putText(image, 'POSTURE', (70, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
        cv2.putText(image, grip, (15, 115),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(image, stance, (15, 140),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

        # Stage data

        cv2.putText(image, 'STAGE', (145, 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
        cv2.putText(image, stage, (130, 45), cv2.FONT_HERSHEY_SIMPLEX,
                    1, (255, 255, 255), 2, cv2.LINE_AA)

        # Display Probability
        cv2.putText(image, f'CONF:{str(round(body_language_prob[np.argmax(body_language_prob)],2))}', (
            130, 68), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

        # Render detections
        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                  mp_drawing.DrawingSpec(
                                      color=(0, 30, 0), thickness=2, circle_radius=2),
                                  mp_drawing.DrawingSpec(
                                      color=(187, 225, 160), thickness=2, circle_radius=2)
                                  )

        cv2.imshow('WorkoutVis', image)

        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
