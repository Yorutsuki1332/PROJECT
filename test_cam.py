import cv2
import time

def test_camera():
    print("Testing camera access...")
    
    # Try different camera indices
    print(f"Trying camera index {-1}")
    cap = cv2.VideoCapture(-1)
    
    if not cap.isOpened():
        print(f"Failed to open camera {-1}")
    else:        
        print(f"Successfully opened camera {-1}")
    
    # Try to read a frame
    ret, frame = cap.read()
    if ret:
        print(f"Successfully read frame from camera {-1}")
        # Save test image
        cv2.imwrite(f'test_camera_{-1}.jpg', frame)
        print(f"Saved test image as test_camera_{-1}.jpg")
    else:
        print(f"Failed to read frame from camera {-1}")
        
    cap.release()
        
    print("Camera test completed")

if __name__ == "__main__":
    test_camera()