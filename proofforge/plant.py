"""The system to be controlled: an inverted pendulum (a pole that falls over).

State x = (theta, omega):
  theta  angle from UPRIGHT (0 = balanced straight up)
  omega  angular velocity

Open-loop dynamics (no control), origin is UNSTABLE -- the pole falls:
  theta_dot = omega
  omega_dot = (g/l) * sin(theta) - damping * omega

With a control torque u:
  omega_dot = (g/l) * sin(theta) - damping * omega + u

The job: invent u(theta, omega) that drives the pole back to upright, AND a
Lyapunov function V(theta, omega) that PROVES it always settles.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class Plant:
    g_over_l: float = 10.0      # gravity / length; larger = falls faster
    damping: float = 0.0        # natural damping (0 = none; harder / more honest)
    # Region of interest over which we demand a proof of stability:
    theta_max: float = 1.0      # rad (~57 deg) around upright
    omega_max: float = 2.0      # rad/s
    dt: float = 0.02            # for demo rollouts only

    def deriv(self, state: np.ndarray, u: np.ndarray | float) -> np.ndarray:
        """Time derivative xdot = f(x, u). Vectorized over rows of `state`."""
        state = np.atleast_2d(np.asarray(state, dtype=float))
        theta, omega = state[:, 0], state[:, 1]
        u = np.asarray(u, dtype=float).reshape(-1)
        theta_dot = omega
        omega_dot = self.g_over_l * np.sin(theta) - self.damping * omega + u
        return np.stack([theta_dot, omega_dot], axis=1)

    def rollout(self, state0, controller, steps: int = 600):
        """Simulate the closed loop for a demo/plot (RK4). controller: X->u."""
        x = np.atleast_2d(np.asarray(state0, dtype=float)).copy()
        traj = [x.copy()]
        for _ in range(steps):
            k1 = self.deriv(x, controller(x))
            k2 = self.deriv(x + 0.5 * self.dt * k1, controller(x + 0.5 * self.dt * k1))
            k3 = self.deriv(x + 0.5 * self.dt * k2, controller(x + 0.5 * self.dt * k2))
            k4 = self.deriv(x + self.dt * k3, controller(x + self.dt * k3))
            x = x + (self.dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
            traj.append(x.copy())
        return np.concatenate(traj, axis=0)

    def grid(self, n_theta: int = 121, n_omega: int = 121, *, exclude_origin: float = 0.0):
        """A dense grid over the region of interest (for verification)."""
        th = np.linspace(-self.theta_max, self.theta_max, n_theta)
        om = np.linspace(-self.omega_max, self.omega_max, n_omega)
        T, O = np.meshgrid(th, om)
        X = np.stack([T.ravel(), O.ravel()], axis=1)
        if exclude_origin > 0:
            keep = np.linalg.norm(X, axis=1) >= exclude_origin
            X = X[keep]
        return X

    def spacing(self, n_theta: int = 121, n_omega: int = 121) -> float:
        """Max grid cell half-diagonal -- used for the verification margin."""
        d_th = (2 * self.theta_max) / (n_theta - 1)
        d_om = (2 * self.omega_max) / (n_omega - 1)
        return 0.5 * float(np.hypot(d_th, d_om))


if __name__ == "__main__":
    p = Plant()
    # Show it is open-loop unstable: no control, a small tilt grows.
    traj = p.rollout([0.15, 0.0], controller=lambda X: np.zeros(len(X)), steps=100)
    print("open-loop |theta| start=0.15 -> end =", f"{abs(traj[-1,0]):.3f}",
          "(grows => unstable, as expected)")
