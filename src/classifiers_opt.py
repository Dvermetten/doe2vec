from random import sample

import tensorflow as tf
from tensorflow.keras import layers, losses
from tensorflow.keras.models import Model
import numpy as np
from keras.layers import Dense, Input, Concatenate, Lambda, Flatten, Dropout
from keras.utils.vis_utils import plot_model
from sklearn.metrics import pairwise_distances
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
import keras.backend as K
from sklearn.metrics import f1_score
import json
from keras.utils import np_utils
from convnd import ConvND
import copy
import os
import sys
if not sys.warnoptions:
    import warnings
    warnings.simplefilter("ignore")
import bbobbenchmarks as bbob
from scipy.stats import qmc

class CustomConnected(Dense):

    def __init__(self,units,connections,**kwargs):
        """Custom dense layer with structural information in the 
        connections.
        """
        #this is matrix A
        self.connections = connections                        

        #initalize the original Dense with all the usual arguments   
        super(CustomConnected,self).__init__(units,**kwargs)  

    def call(self, inputs):
        output = K.dot(inputs, self.kernel * self.connections)
        if self.use_bias:
            output = K.bias_add(output, self.bias)
        if self.activation is not None:
            output = self.activation(output)
        return output

class StructuralInformedDense(Model):
    def __init__(self, num_knn_layers, layer_sizes, num_classes, sample_size, DOE, overlap=False):
        """Dense classifier with custom connections based on the DOE between input and first hidden layer.
        """
        super(StructuralInformedDense, self).__init__()
        self.layer_sizes = layer_sizes
        self.num_knn_layers = num_knn_layers
        self.DOE = DOE
        self.num_classes = num_classes
        self.dim = self.DOE.shape[1]
        self.sample_size = sample_size
        self.overlap = overlap
        self.classifier = self._classifier()

    def knnLayer(self, input, sample_size, locations, overlap=False, k=None):
        #Generalize like knn-cnn, with strides (include points once / always)
        #allow for stacking, give new location (by averaging) to new point
        if k == None:
            k = self.dim * 2 + 1
        output_size = self.sample_size
        pair_distances = pairwise_distances(locations, metric='cityblock')
        if (overlap):
            connections = np.zeros((sample_size, sample_size))
            new_locations = np.zeros((sample_size,self.dim))
            for i in range(0,len(locations)):
                indexes_to_use = np.argsort(pair_distances[i,:])[:k]
                connections[indexes_to_use, i] = 1
                new_locations[i] = np.mean(locations[indexes_to_use], axis=0)
        else:
            indexes_used = np.zeros(len(locations), dtype=bool)
            groups = []
            for i in range(0,len(locations)):
                if (not indexes_used[i]):
                    pair_distances = pairwise_distances(locations, metric='cityblock')
                    #update the used indexes
                    indexes_to_use = np.argsort(pair_distances[i,:])[:k]
                    indexes_used[indexes_to_use] = True
                    groups.append(indexes_to_use)
            connections = np.zeros((sample_size,len(groups)))
            new_locations = np.zeros((len(groups),self.dim))
            for i in range(0,len(groups)):
                connections[groups[i], i] = 1
                new_locations[i] = np.mean(locations[groups[i]], axis=0)
            output_size = len(groups)
        tf_connections = tf.convert_to_tensor(connections, dtype=tf.float32)

        x = CustomConnected(output_size, tf_connections, activation="relu")(input)
        return x, new_locations

    def _classifier(self):
        '''Create a Dense network with shape information from the DOE'''
        #we use knowledge of the space filling design to determine the distance threshold

        
        inputTensor = Input((self.sample_size,))
        x, new_locations = self.knnLayer(inputTensor, self.sample_size, self.DOE, self.overlap)
        for i in range(self.num_knn_layers - 1):
            x, new_locations = self.knnLayer(x, len(new_locations), new_locations, self.overlap)

        for num_nodes in self.layer_sizes:
            x = Dense(num_nodes, activation="relu")(x)
        x = Dropout(0.2)(x)
        x = Dense(self.num_classes, activation="sigmoid")(x)
        classifier = tf.keras.Model(inputTensor, x, name="StructuralInformedDense")
        return classifier

    def call(self, x):
        return self.classifier(x)



dim = 10
m=10
sampler = qmc.Sobol(d=dim, scramble=False, seed=42)
sample = sampler.random_base2(m=m)
sample = sample * 10 - 5
print("#samples ", len(sample))


X = []
mesh_X = []
multim_label = []
global_label = []
funnel_label = []
for i in range(120):
    for f in range(1, 25):
        fun, opt = bbob.instantiate(f, i)
        bbob_y = np.asarray(list(map(fun, sample)))
        array_x = (bbob_y.flatten() - np.min(bbob_y)) / (
            np.max(bbob_y) - np.min(bbob_y)
        )
        X.append(array_x)
        if (dim < 4):
            mesh_X.append(np.reshape(array_x, (nx,)*dim))
        if f in [1,2]:
            multim_label.append("none")
            global_label.append("none")
            funnel_label.append("yes")
        elif f in [3,4]:
            multim_label.append("high")
            global_label.append("strong")
            funnel_label.append("yes")
        elif f in [8,9]:
            multim_label.append("low")
            global_label.append("none")
            funnel_label.append("yes")
        elif f in [5,6,7,10,11,12,13,14]:
            multim_label.append("none")
            global_label.append("none")
            funnel_label.append("yes")
        elif f in [15,19]:
            multim_label.append("high")
            global_label.append("strong")
            funnel_label.append("yes")
        elif f in [16]:
            multim_label.append("high")
            global_label.append("medium")
            funnel_label.append("none")
        elif f in [17,18]:
            multim_label.append("high")
            global_label.append("medium")
            funnel_label.append("yes")
        elif f in [20]:
            multim_label.append("medium")
            global_label.append("deceptive")
            funnel_label.append("yes")
        elif f in [21]:
            multim_label.append("medium")
            global_label.append("none")
            funnel_label.append("none")
        elif f in [22]:
            multim_label.append("low")
            global_label.append("none")
            funnel_label.append("none")
        elif f in [23]:
            multim_label.append("high")
            global_label.append("none")
            funnel_label.append("none")
        elif f in [24]:
            multim_label.append("high")
            global_label.append("weak")
            funnel_label.append("yes")

                
X = np.array(X)
if (dim < 4):
    mesh_X = np.array(mesh_X)
y_1 = np.array(multim_label)
y_2 = np.array(global_label)
y_3 = np.array(funnel_label)
#use LabelEncoder or OneHotEncoder
enc1 = LabelEncoder()
enc2 = LabelEncoder()
enc3 = LabelEncoder()


y_1 = enc1.fit_transform(y_1)
y_2 = enc2.fit_transform(y_2)
y_3 = enc3.fit_transform(y_3)

dummy_y1 = np_utils.to_categorical(y_1)
dummy_y2 = np_utils.to_categorical(y_2)
dummy_y3 = np_utils.to_categorical(y_3)
test_size = 20*25

X_train = X[:-test_size]
X_test = X[-test_size:]

dummy_ys = [dummy_y1,dummy_y2,dummy_y3]
ys = [y_1,y_2,y_3]
probs = ["multimodal", "global", "funnel"]

def runClassifier(conf):
    f1_results = []
    
    for i in [0,1,2]:
        y = dummy_ys[i]
        real_y = ys[i]
        prob = probs[i]

        #StructuralInformedDense
        cf = StructuralInformedDense(int(conf['knn_layers']), [int(conf['dense'])],y.shape[1],X.shape[1],sample,conf['overlap'])
        cf.compile(loss='binary_crossentropy', optimizer='adam')
        cf.fit(
            X_train, y[:-test_size],
            epochs=50,
            batch_size=32,
            shuffle=True,
            validation_data=(X_test, y[-test_size:]),
            verbose=0
        )
        y_dummy_pred = cf.predict(X_test)
        y_pred = np.argmax(y_dummy_pred, axis=1)
        score = f1_score(real_y[-test_size:], y_pred, average='macro')
        print("new",dim, prob, score)
        f1_results.append(score)
    return -1*np.mean(f1_results)

if __name__ == "__main__":
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

    """Classification experiment for BBOB
    """
    
    seed=0
    from bayes_optim import BO, DiscreteSpace, IntegerSpace, RealSpace
    from bayes_optim.surrogate import RandomForest

    knn = IntegerSpace([1, 5], var_name="knn_layers")
    dense = IntegerSpace([32,512], var_name="dense")
    overlap = DiscreteSpace([True, False], var_name="overlap")
    search_space = knn + dense + overlap

    model = RandomForest(levels=search_space.levels)
    opt = BO(
        search_space=search_space,
        obj_fun=runClassifier,
        model=model,
        max_FEs=50,
        data_file = "optdata.txt",
        DoE_size=3,  # the initial DoE size
        eval_type="dict",
        acquisition_fun="MGFI",
        acquisition_par={"t": 2},
        n_job=1,  # number of processes
        n_point=1,  # number of the candidate solution proposed in each iteration
        verbose=True,  # turn this off, if you prefer no output
    )
    xopt, fopt, stop_dict = opt.run()

    print("xopt: {}".format(xopt))
    print("fopt: {}".format(fopt))
    print("stop criteria: {}".format(stop_dict))

    
    
