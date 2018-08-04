import numpy as np
import tensorflow as tf

from fifa_ratings_predictor.data_methods import normalise_features


class NeuralNet:
    def __init__(self, hidden_nodes=8, keep_prob=1.0, learning_rate=0.001):
        self.hidden_nodes = hidden_nodes
        self.keep_prob_value = keep_prob
        self.learning_rate = learning_rate

        self.graph = tf.Graph()
        self.input = None
        self.keep_prob = None
        self.target = None
        self.loss = None
        self.train = None
        self.output = None
        self.training_summary = None
        self.validation_summary = None

        self.build_model()

    def build_model(self):
        with self.graph.as_default():
            self.input = tf.placeholder(tf.float32, shape=[None, 36], name='input')
            self.target = tf.placeholder(tf.float32, shape=[None, 3], name='target')
            self.keep_prob = tf.placeholder(tf.float32, name='keep_prob')

            hidden_layer = tf.layers.dense(self.input, 16, activation=tf.nn.relu, name="hidden_layer")
            hidden_layer2 = tf.layers.dense(hidden_layer, 8, activation=tf.nn.relu, name="hidden_layer2")
            self.output = tf.layers.dense(hidden_layer2, 3, name="output")
            self.output = tf.nn.softmax(self.output, name='softmax')

            with tf.name_scope('losses') as scope:
                self.loss = tf.losses.absolute_difference(self.target, self.output)

                self.train = tf.train.MomentumOptimizer(self.learning_rate, 0.99).minimize(self.loss)

            self.training_summary = tf.summary.scalar("training_accuracy", self.loss)
            self.validation_summary = tf.summary.scalar("validation_accuracy", self.loss)

    @staticmethod
    def init_saver(sess):
        writer = tf.summary.FileWriter('./tf-log-SP1/', sess.graph)
        saver = tf.train.Saver(max_to_keep=1)
        return writer, saver

    def train_model(self, X, y, X_val, y_val, model_name):

        best_val_loss = 0.05

        with tf.Session(graph=self.graph) as sess:

            writer, saver = self.init_saver(sess)

            sess.run(tf.global_variables_initializer())

            for i in range(40000):

                feed_dict = {self.input: X, self.target: y, self.keep_prob: 0.8}

                _, current_loss, train_sum = sess.run([self.train, self.loss, self.training_summary],
                                                      feed_dict=feed_dict)

                if i % 1000 == 0:
                    val_loss, val_sum = sess.run([self.loss, self.validation_summary],
                                                 feed_dict={self.input: X_val, self.target: y_val, self.keep_prob: 1.0})
                    writer.add_summary(val_sum, i)
                    writer.add_summary(train_sum, i)

                    print(i, current_loss, val_loss)
                    if val_loss < best_val_loss:
                        best_val_loss = val_loss
                        saver.save(sess, model_name)

    def predict(self, X, model_name):

        with tf.Session() as sess:
            saver = tf.train.import_meta_graph(model_name + '.meta')
            saver.restore(sess, model_name)
            graph = tf.get_default_graph()
            input = graph.get_tensor_by_name('input:0')
            keep_prob = graph.get_tensor_by_name('keep_prob:0')
            output = graph.get_tensor_by_name('softmax:0')
            feed_dict = {input: X, keep_prob: 1.0}
            predictions = sess.run(output, feed_dict=feed_dict)

        return predictions


if __name__ == '__main__':

    tf.set_random_seed(8)
    np.random.seed(8)

    league = 'F1'

    inputs = np.vstack((np.load('./data/lineup-data/' + league + '/processed-numpy-arrays/feature-vectors-13-14.npy'),
                        np.load('./data/lineup-data/' + league + '/processed-numpy-arrays/feature-vectors-14-15.npy'),
                        np.load('./data/lineup-data/' + league + '/processed-numpy-arrays/feature-vectors-15-16.npy'),
                        np.load('./data/lineup-data/' + league + '/processed-numpy-arrays/feature-vectors-16-17.npy')))
    inputs = normalise_features(inputs)
    outputs = np.vstack((np.load('./data/lineup-data/' + league + '/processed-numpy-arrays/targets-13-14.npy'),
                        np.load('./data/lineup-data/' + league + '/processed-numpy-arrays/targets-14-15.npy'),
                        np.load('./data/lineup-data/' + league + '/processed-numpy-arrays/targets-15-16.npy'),
                        np.load('./data/lineup-data/' + league + '/processed-numpy-arrays/targets-16-17.npy'))).reshape(-1, 3)

    nan_rows = np.where(outputs != outputs)[0]

    inputs = np.delete(inputs, nan_rows, axis=0)
    outputs = np.delete(outputs, nan_rows, axis=0)

    outputs = 1 / outputs

    net = NeuralNet()

    net.train_model(inputs[:-10], outputs[:-10], inputs[-10:], outputs[-10:], model_name='./models/' + league +
                                                                                    '/deep')

    net = NeuralNet()

    predictions = net.predict(inputs[-50:], model_name='./models/' + league + '/deep')

    for i, j in zip(predictions, outputs[-50:]):
        print(i)
        print(j)
