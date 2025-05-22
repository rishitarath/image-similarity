import cv2
import os
import rawpy
import imageio
from skimage.metrics import structural_similarity as ssim
from tkinter import Tk, messagebox
import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter.filedialog import askopenfilename


def drag_and_drop_workflow():
    dropped_files = {"reference": None, "current": None}
    labels = {}

    def handle_drop(event, label_type):
        path = event.data.strip('{}')
        if os.path.isfile(path):
            dropped_files[label_type] = path
            labels[label_type].config(text=f"{label_type.capitalize()} Image:\n{os.path.basename(path)}")
        else:
            messagebox.showerror("Invalid File", "Please drop a valid file.")

    def capture_image(label_type):
        path = f"{label_type}_product.jpg"
        result = CapturePhoto(path)
        if result:
            dropped_files[label_type] = result
            labels[label_type].config(text=f"{label_type.capitalize()} Image:\n{os.path.basename(result)}")

    def compare_images():
        if not dropped_files["reference"] or not dropped_files["current"]:
            messagebox.showwarning("Missing Images", "Please provide both images.")
            return

        sim = CalculateImageSimilarity(dropped_files["reference"], dropped_files["current"])
        if sim == -1:
            messagebox.showerror("Error", "Failed to calculate similarity.")
        else:
            messagebox.showinfo("Similarity", f"Similarity: {sim:.2f}%")

    root = TkinterDnD.Tk()
    root.title("Image Comparison - Drag, Drop or Capture")
    root.geometry("500x500")

    for kind in ["reference", "current"]:
        from tkinter import Frame  # or from tkinterdnd2 import TkinterDnD
        frame = Frame(root)
        
        frame.pack(pady=15)

        label = tk.Label(frame, text=f"Drop {kind.capitalize()} Image Here", bg="lightgray", width=60, height=5)
        label.pack()
        label.drop_target_register(DND_FILES)
        label.dnd_bind('<<Drop>>', lambda e, k=kind: handle_drop(e, k))
        labels[kind] = label

        button = tk.Button(frame, text=f"Capture {kind.capitalize()} Image", command=lambda k=kind: capture_image(k))
        button.pack()

    tk.Button(root, text="Compare Images", command=compare_images).pack(pady=30)

    root.mainloop()


def load_image(image_path, grayscale=False):
    ext = os.path.splitext(image_path)[1].lower()
    if ext == ".dng":
        try:
            raw = rawpy.imread(image_path)
            rgb = raw.postprocess()
            if grayscale:
                return cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
            else:
                return rgb
        except Exception as e:
            print(f"Error loading RAW image {image_path}: {e}")
            return None
    else:
        flag = cv2.IMREAD_GRAYSCALE if grayscale else cv2.IMREAD_COLOR
        img = cv2.imread(image_path, flag)
        if img is None:
            print(f"Error: Failed to load image from {image_path}")
        return img


def CapturePhoto(save_path='captured_product.jpg'):
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Cannot open camera")
        return None

    print("Press 'c' to capture, ESC to exit")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        cv2.imshow("Camera - Press c to capture", frame)

        key = cv2.waitKey(1)
        if key == ord('c'):
            cv2.imwrite(save_path, frame)
            print(f"Captured image saved to {save_path}")
            break
        elif key == 27:
            print("Capture cancelled")
            save_path = None
            break

    cap.release()
    cv2.destroyAllWindows()
    return save_path


def CalculateImageSimilarity(image_path1, image_path2):
    try:
        img1 = load_image(image_path1, grayscale=True)
        img2 = load_image(image_path2, grayscale=True)

        if img1 is None or img2 is None:
            print("There is an error loading the images or the images do not exist.")
            return -1

        if img1.shape != img2.shape:
            common_size = (300, 300)
            img1 = cv2.resize(img1, common_size)
            img2 = cv2.resize(img2, common_size)

        similarity = ssim(img1, img2)
        return similarity * 100

    except Exception as e:
        print("An error occurred:", e)
        return -1


def run_manual_workflow():
    Tk().withdraw()

    print("Select Reference Image Option:")
    print("1. Select from file")
    print("2. Capture from webcam")
    choice = input("Enter 1 or 2: ").strip()

    if choice == '1':
        ReferenceImagePath = askopenfilename(title="Select reference product image",
                                             filetypes=[("All Files", "*.*")])
        if not ReferenceImagePath:
            print("No reference image selected, exiting.")
            return

    elif choice == '2':
        ReferenceImagePath = CapturePhoto('reference_product.jpg')
        if ReferenceImagePath is None:
            print("No reference image captured, exiting.")
            return

    else:
        print("Invalid choice. Exiting.")
        return

    print("Select Current Image Option:")
    print("1. Select from file")
    print("2. Capture from webcam")
    choice2 = input("Enter 1 or 2: ").strip()

    if choice2 == '1':
        CurrentImagePath = askopenfilename(title="Select current product image",
                                          filetypes=[("All Files", "*.*")])
        if not CurrentImagePath:
            print("No current image selected, exiting.")
            return

    elif choice2 == '2':
        CurrentImagePath = CapturePhoto('current_product.jpg')
        if CurrentImagePath is None:
            print("No current image captured, exiting.")
            return

    else:
        print("Invalid choice. Exiting.")
        return

    similarity = CalculateImageSimilarity(ReferenceImagePath, CurrentImagePath)

    if similarity == -1:
        print("Could not calculate similarity.")
    else:
        print(f"Similarity: {similarity:.2f}%")


def main():
    print("Choose mode:")
    print("1. Manual selection / capture")
    print("2. Drag-and-drop GUI")

    choice = input("Enter 1 or 2: ").strip()

    if choice == '1':
        run_manual_workflow()
    elif choice == '2':
        drag_and_drop_workflow()
    else:
        print("Invalid choice. Exiting.")


if __name__ == "__main__":
    main()
