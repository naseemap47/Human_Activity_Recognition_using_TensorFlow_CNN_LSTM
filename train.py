import random
import numpy as np
import tensorflow as tf
import os
import matplotlib.pyplot as plt
import argparse

from sklearn.model_selection import train_test_split
from tensorflow.keras.utils import to_categorical
from keras.callbacks import EarlyStopping
from tensorflow.keras.utils import plot_model

from utils import create_dataset
from models import convlstm_model, LRCN_model

seed_constant = 27
np.random.seed(seed_constant)
random.seed(seed_constant)
tf.random.set_seed(seed_constant)

ap = argparse.ArgumentParser()
ap.add_argument("-i", "--dataset", type=str, required=True,
                help="path to csv Data")
# Specify the number of frames of a video that will be fed to the model as one sequence.
ap.add_argument("-l", "--seq_len", type=int, default=20,
                help="length of Sequence")

ap.add_argument("-s", "--size", type=int, default=64,
                help="Specify the height and width to which each video frame will be resized in our dataset.")
ap.add_argument("-m", "--model", type=str,  default='LRCN',
                choices=['convLSTM', 'LRCN'],
                help="select model type convLSTM or LRCN")

args = vars(ap.parse_args())
DATASET_DIR = args["dataset"]
SEQUENCE_LENGTH = args["seq_len"]
IMAGE_SIZE = args["size"]
model_type = args["model"]

# Specify the list containing the names of the classes used for training. Feel free to choose any set of classes.
CLASSES_LIST = sorted(os.listdir(DATASET_DIR))

# Create the dataset.
features, labels, video_files_paths = create_dataset(
    CLASSES_LIST, DATASET_DIR, SEQUENCE_LENGTH, IMAGE_SIZE)

# Using Keras's to_categorical method to convert labels into one-hot-encoded vectors
one_hot_encoded_labels = to_categorical(labels)

# Split the Data into Train ( 80% ) and Test Set ( 20% ).
features_train, features_test, labels_train, labels_test = train_test_split(
    features, one_hot_encoded_labels, test_size=0.2, shuffle=True, random_state=seed_constant)

if model_type == 'convLSTM':
    print("[INFO] Selected convLSTM Model")
    model = convlstm_model(SEQUENCE_LENGTH, IMAGE_SIZE, CLASSES_LIST)
    print("convLSTM Created Successfully!")
elif model_type == 'LRCN':
    print("[INFO] Selected LRCN Model")
    model = LRCN_model(SEQUENCE_LENGTH, IMAGE_SIZE, CLASSES_LIST)
    print("LRCN Created Successfully!")
else:
    print('[INFO] Model NOT Choosen!!')

# Plot the structure of the contructed model.
plot_model(model, to_file=f'{model_type}_model_str.png',
           show_shapes=True, show_layer_names=True)

# Create an Instance of Early Stopping Callback
early_stopping_callback = EarlyStopping(
    monitor='val_loss', patience=15, mode='min', restore_best_weights=True)

# Compile the model and specify loss function, optimizer and metrics values to the model
model.compile(loss='categorical_crossentropy',
              optimizer='Adam', metrics=["accuracy"])

# Start training the model.
history = model.fit(x=features_train, y=labels_train, epochs=70, batch_size=4,
                    shuffle=True, validation_split=0.2, callbacks=[early_stopping_callback])

# Evaluate the trained model.
model_evaluation_history = model.evaluate(features_test, labels_test)

# Get the loss and accuracy from model_evaluation_history.
model_evaluation_loss, model_evaluation_accuracy = model_evaluation_history

# Define a useful name for our model to make it easy for us while navigating through multiple saved models.
model_file_name = f'{model_type}_model_loss_{model_evaluation_loss:.3}_acc_{model_evaluation_accuracy:.3}.h5'

# Save your Model.
model.save(model_file_name)
print(f'[INFO] Model {model_file_name} saved Successfully..')


# Plot History
metric_loss = history.history['loss']
metric_val_loss = history.history['val_loss']
metric_accuracy = history.history['accuracy']
metric_val_accuracy = history.history['val_accuracy']

# Construct a range object which will be used as x-axis (horizontal plane) of the graph.
epochs = range(len(metric_loss))

# Plot the Graph.
plt.plot(epochs, metric_loss, 'blue', label=metric_loss)
plt.plot(epochs, metric_val_loss, 'red', label=metric_val_loss)
plt.plot(epochs, metric_accuracy, 'blue', label=metric_accuracy)
plt.plot(epochs, metric_val_accuracy, 'green', label=metric_val_accuracy)

# Add title to the plot.
plt.title(str('Model Metrics'))

# Add legend to the plot.
plt.legend(['loss', 'val_loss', 'accuracy', 'val_accuracy'])

# If the plot already exist, remove
plot_png = os.path.exists('metrics.png')
if plot_png:
    os.remove('metrics.png')
    plt.savefig('metrics.png', bbox_inches='tight')
else:
    plt.savefig(f'{model_type}_metrics.png', bbox_inches='tight')
print('[INFO] Successfully Saved metrics.png')
