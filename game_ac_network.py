# -*- coding: utf-8 -*-
import tensorflow as tf
import numpy as np

# Actor-Critic Network (Policy network and Value network)

class GameACNetwork(object):
  def __init__(self, action_size):
    with tf.device("/cpu:0"):
      self._action_size = action_size
      
      self.W_conv1 = self._weight_variable([8, 8, 4, 16])  # stride=4
      self.b_conv1 = self._bias_variable([16])

      self.W_conv2 = self._weight_variable([4, 4, 16, 32]) # stride=2
      self.b_conv2 = self._bias_variable([32])

      self.W_fc1 = self._weight_variable([2592, 256])
      self.b_fc1 = self._bias_variable([256])

      # weight for policy output layer
      self.W_fc2 = self._weight_variable([256, action_size])
      self.b_fc2 = self._bias_variable([action_size])

      # weight for value output layer
      self.W_fc3 = self._weight_variable([256, 1])
      self.b_fc3 = self._bias_variable([1])

      # state (input)
      self.s = tf.placeholder("float", [1, 84, 84, 4])
    
      h_conv1 = tf.nn.relu(self._conv2d(self.s, self.W_conv1, 4) + self.b_conv1)
      h_conv2 = tf.nn.relu(self._conv2d(h_conv1, self.W_conv2, 2) + self.b_conv2)

      h_conv2_flat = tf.reshape(h_conv2, [1, 2592])
      h_fc1 = tf.nn.relu(tf.matmul(h_conv2_flat, self.W_fc1) + self.b_fc1)

      # policy (output)
      self.pi = tf.nn.softmax(tf.matmul(h_fc1, self.W_fc2) + self.b_fc2)
      # value (output)
      self.v = tf.matmul(h_fc1, self.W_fc3) + self.b_fc3

  def prepare_loss(self, entropy_beta):
    with tf.device("/cpu:0"):
      # taken action (input for policy)
      self.a = tf.placeholder("float", [1, self._action_size])
    
      # temporary difference (R-V) (input for policy)
      self.td = tf.placeholder("float", [1])
      # policy entropy
      entropy = -tf.reduce_sum(self.pi * tf.log(self.pi))

      # policy loss (output)  (add minus, because this is for gradient ascent)
      # (Learning rate for Actor is half of Critic's, so multiply by 0.5)
      policy_loss = -0.5 * ( tf.reduce_sum( tf.mul( tf.log(self.pi), self.a ) ) * self.td +
                             entropy * entropy_beta )

      # R (input for value)
      self.r = tf.placeholder("float", [1])
      # value loss (output)
      value_loss = tf.nn.l2_loss(self.r - self.v)

      # gradienet of policy and value are summed up
      self.total_loss = policy_loss + value_loss

  def run_policy(self, sess, s_t):
    pi_out = sess.run( self.pi, feed_dict = {self.s : [s_t]} )
    return pi_out[0]

  def run_value(self, sess, s_t):
    v_out = sess.run( self.v, feed_dict = {self.s : [s_t]} )
    return v_out[0][0] # output is scalar

  def get_vars(self):
    return [self.W_conv1, self.b_conv1,
            self.W_conv2, self.b_conv2,
            self.W_fc1, self.b_fc1,
            self.W_fc2, self.b_fc2,
            self.W_fc3, self.b_fc3]

  def sync_from(self, src_netowrk, name=None):
    src_vars = src_netowrk.get_vars()
    dst_vars = self.get_vars()

    sync_ops = []

    with tf.device("/cpu:0"):
      with tf.op_scope([], name, "GameACNetwork") as name:
        for(src_var, dst_var) in zip(src_vars, dst_vars):
          sync_op = tf.assign(dst_var, src_var)
          sync_ops.append(sync_op)

        return tf.group(*sync_ops, name=name)

  def _weight_variable(self, shape):
    initial = tf.truncated_normal(shape, stddev = 0.01)
    return tf.Variable(initial)

  def _bias_variable(self, shape):
    initial = tf.constant(0.0, shape = shape)
    return tf.Variable(initial)

  def _conv2d(self, x, W, stride):
    return tf.nn.conv2d(x, W, strides = [1, stride, stride, 1], padding = "VALID")

  def _debug_save_sub(self, sess, prefix, var, name):
    var_val = var.eval(sess)
    var_val = np.reshape(var_val, (1, np.product(var_val.shape)))        
    np.savetxt('./' + prefix + '_' + name + '.csv', var_val, delimiter=',')

  def debug_save(self, sess, prefix):
    self._save_sub(sess, prefix, self.W_conv1, "W_conv1")
    self._save_sub(sess, prefix, self.b_conv1, "b_conv1")
    self._save_sub(sess, prefix, self.W_conv2, "W_conv2")
    self._save_sub(sess, prefix, self.b_conv2, "b_conv2")
    self._save_sub(sess, prefix, self.W_fc1, "W_fc1")
    self._save_sub(sess, prefix, self.b_fc1, "b_fc1")
    self._save_sub(sess, prefix, self.W_fc2, "W_fc2")
    self._save_sub(sess, prefix, self.b_fc2, "b_fc2")
    self._save_sub(sess, prefix, self.W_fc3, "W_fc3")
    self._save_sub(sess, prefix, self.b_fc3, "b_fc3")
