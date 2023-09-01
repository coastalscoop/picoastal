import argparse
import numpy as np
import cv2
from glob import glob
from natsort import natsorted
from tqdm import tqdm
from skimage.util import img_as_float64  # Add this import

class Welford:
    def __init__(self):
        self.k = 0
        self.M1 = 0
        self.M2 = 0

    def add(self, x):
        self.k += 1
        delta = x - self.M1
        self.M1 += delta / self.k
        delta2 = x - self.M1
        self.M2 += delta * delta2

    @property
    def mean(self):
        return self.M1

    @property
    def var(self):
        if self.k < 2:
            return np.nan
        return self.M2 / (self.k - 1)

def process_images(image_paths, output_folder):
    image_count = len(image_paths)
    if image_count == 0:
        print("No images found in the input folder.")
        return

    # Initialize the accumulators for average and variance
    avg_image = np.zeros(cv2.imread(image_paths[0]).shape, dtype=np.float64)
    w = Welford()
    
    # Initialize the darkest image with white pixels
    darkest_image = 255 * np.ones(cv2.imread(image_paths[0]).shape, dtype=np.uint8)
    
    # Initialize the brightest image with black pixels
    brightest_image = np.zeros(cv2.imread(image_paths[0]).shape, dtype=np.uint8)

    for image_path in tqdm(image_paths, desc="Processing Images"):
        image = cv2.imread(image_path)
        
        # Update the average image
        avg_image += (image.astype(np.float64) - avg_image) / (image_count + 1)
        
        # Update the variance image using Welford's method
        img_as_float = img_as_float64(image)
        w.add(img_as_float)
        variance_image = w.var

        # Update the darkest image
        darkest_image = np.minimum(darkest_image, image)
        
        # Update the brightest image
        brightest_image = np.maximum(brightest_image, image)

    # Scale the variance values as per the provided mechanics
    min_var = variance_image.min()
    max_var = variance_image.max()
    scaled_variance_image = ((variance_image - min_var) / (max_var - min_var) * 255).astype(np.uint8)

    # Save the processed images
    #cv2.imwrite(f"{output_folder}/average.png", avg_image.astype(np.uint8))
    #cv2.imwrite(f"{output_folder}/variance.png", scaled_variance_image)
    #cv2.imwrite(f"{output_folder}/darkest.png", darkest_image)
    #cv2.imwrite(f"{output_folder}/brightest.png", brightest_image)
    cv2.imwrite(args.timex, avg_image.astype(np.uint8))
    cv2.imwrite(args.variance, scaled_variance_image)
    cv2.imwrite(args.darkest, darkest_image)
    cv2.imwrite(args.brightest, brightest_image)

if __name__ == "__main__":
    # Argument parser
    parser = argparse.ArgumentParser()

    # Input folder
    parser.add_argument("--input", "-i",
                        action="store",
                        dest="input",
                        required=True,
                        help="Input folder with images file.")

    parser.add_argument("--brightest", "-b",
                        action="store",
                        dest="brightest",
                        default="brightest.png",
                        required=False,
                        help="Output name for brightest image.",)

    parser.add_argument("--darkest", "-d",
                        action="store",
                        dest="darkest",
                        default="darkest.png",
                        required=False,
                        help="Output name for darkest image.",)
                        
    parser.add_argument("--timex", "-t",
                        action="store",
                        dest="timex",
                        default="timex.png",
                        required=False,
                        help="Output name for timex image.",)

    parser.add_argument("--variance", "-v",
                        action="store",
                        dest="variance",
                        default="variance.png",
                        required=False,
                        help="Output name for variance image.",)
    # Output folder
    parser.add_argument("--output", "-o",
                        action="store",
                        dest="output",
                        default="output",
                        required=False,
                        help="Output folder for processed images.")
                        
                        

    args = parser.parse_args()

    # Get a list of image file paths and sort them
    image_paths = natsorted(glob(args.input + "/*"))

    # Create the output folder if it doesn't exist
    import os
    os.makedirs(args.output, exist_ok=True)

    # Process the images iteratively
    process_images(image_paths, args.output)

    print("\nImage processing completed.\n")

