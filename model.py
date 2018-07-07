import numpy as np
import tensorflow as tf


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
        writer = tf.summary.FileWriter('./tf-log/', sess.graph)
        saver = tf.train.Saver(max_to_keep=1)
        return writer, saver

    def train_model(self, X, y, X_val, y_val):

        best_val_loss = 0.038

        with tf.Session(graph=self.graph) as sess:

            writer, saver = self.init_saver(sess)

            sess.run(tf.global_variables_initializer())

            for i in range(50000):

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
                        saver.save(sess, './deep-models/deep')

    def predict(self, X, model_name='deep'):

        with tf.Session() as sess:
            saver = tf.train.import_meta_graph('./deep-models/' + model_name + '.meta')
            saver.restore(sess, './deep-models/' + model_name)
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

    inputs = np.load('feature_vectors.npy')
    max_input = 100  # np.max(inputs)
    min_input = 50  # np.min(inputs[np.nonzero(inputs)])
    inputs = ((inputs - min_input) / (max_input - min_input)).clip(min=0)
    outputs = np.load('targets_odds.npy').reshape(-1, 3)
    outputs = 1 / outputs

    net = NeuralNet()

    net.train_model(inputs[:-100:2], outputs[:-100:2], inputs[-100::2], outputs[-100::2])

    net = NeuralNet()

    predictions = net.predict(inputs[-100::2])

    for i, j in zip(predictions, outputs[-100::2]):
        print(1 / i)
        print(1 / j)
