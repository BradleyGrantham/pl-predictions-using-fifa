import numpy as np
import tensorflow as tf


class NeuralNet:
    def __init__(self, hidden_nodes=8, keep_prob=1.0, learning_rate=0.01):
        self.hidden_nodes = hidden_nodes
        self.keep_prob = keep_prob
        self.learning_rate = learning_rate

        self.graph = tf.Graph()
        self.input = None
        self.target = None
        self.loss = None
        self.train = None
        self.output = None

        self.build_model()
        self.init_saver()

    def build_model(self):
        with self.graph.as_default():
            self.input = tf.placeholder(tf.float32, shape=[None, 34], name='input')
            self.target = tf.placeholder(tf.float32, shape=[None, 1], name='target')

            hidden_layer = tf.layers.dense(self.input, 6, activation=tf.nn.relu, name="hidden_layer")
            self.output = tf.layers.dense(hidden_layer, 1, name="output")

            self.loss = tf.losses.mean_squared_error(self.target, self.output)

            self.train = tf.train.GradientDescentOptimizer(self.learning_rate).minimize(self.loss)

    def init_saver(self):
        pass

    def train_model(self, X, y, X_val, y_val):

        with self.graph.as_default():
            with tf.Session() as sess:

                    writer = tf.summary.FileWriter('./log/', sess.graph)
                    sess.run(tf.global_variables_initializer())

                    for i in range(20000):

                        feed_dict = {self.input: X, self.target: y}

                        _, current_loss = sess.run([self.train, self.loss], feed_dict=feed_dict)

                        # print(current_loss)

                        if i % 1000 == 0:
                            val_loss = sess.run(self.loss, feed_dict={self.input: X_val, self.target: y_val})
                            print(current_loss, val_loss)


                    writer.close()

                    predictions = []

                    for x_, y_ in zip(X_val, y_val):

                        predictions.append((self.predict(sess, x_.reshape(1, 34)))[0][0][0])


        return predictions

    def predict(self, sess, X):

        feed_dict = {self.input: X}

        result = sess.run([self.output], feed_dict=feed_dict)

        return result


if __name__ == '__main__':

    inputs = np.load('feature_vectors.npy')
    max_input = 100  # np.max(inputs)
    min_input = 50  # np.min(inputs[np.nonzero(inputs)])
    inputs = ((inputs - min_input) / (max_input - min_input)).clip(min=0)
    outputs = np.load('targets.npy').reshape(-1, 1)

    net = NeuralNet()

    predictions = net.train_model(inputs[:720], outputs[:720], inputs[720:], outputs[720:])
