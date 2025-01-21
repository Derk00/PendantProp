from analysis.models import szyszkowski, szyszkowski_model
from analysis.active_learning import Baysu
import jax.numpy as jnp
import matplotlib.pyplot as plt
from jax import random
import jax
jax.config.update("jax_enable_x64", True)
## toy example
cmc_true = 0.008 # M
gamma_max_true = 3.5/1000000 # mol/m2
Kad_true = 4000 # L/mol
theta_true = (cmc_true, gamma_max_true, Kad_true)

cS_true = jnp.linspace(0, 2*cmc_true, 100)
g_true = szyszkowski(cS0=cS_true, theta=theta_true)

# Initialize RNG key
rng_key = random.PRNGKey(0)

# Add noise to g_true
noise = random.normal(key=rng_key, shape=g_true.shape) * 0.001
g_noisy = g_true + noise

# Select 4 sample points
n_samples = 6
sample_indices = jnp.linspace(10, len(cS_true) - 1, n_samples, dtype=int)
cS_samples = cS_true[sample_indices]
g_samples = g_noisy[sample_indices]

# Add an artificial outlier
# g_samples = g_samples.at[1].set(g_samples[1] + 0.05)  # Adding a significant outlier

obs = (cS_samples, g_samples)

print("test")

# baysu
# parameters = ["cmc", "gamma_max", "Kad"]
# baysu = Baysu(model=szyszkowski_model, parameters=parameters)

# for round in [1,2,3,4]:
#     baysu.fit(obs=obs, outlier_check=True)
#     x, y = baysu.bayesian_suggestion()
#     baysu.plot_suggestion(x, filename=f"round_{round}")
#     obs = (jnp.append(obs[0], x), jnp.append(obs[1], y))

    
# baysu.plot_suggestion(x_suggestion=x, filename="round 1")
# props = baysu.get_properties()
# print(props)




# Plotting
# plt.figure(figsize=(8, 6))
# plt.plot(cS_true, g_true, label='true')
# plt.scatter(cS_samples, g_samples, color='red', label='sample')
# plt.xlabel('Concentration (M)')
# plt.ylabel('Surface Tension (N/m)')
# plt.title('Szyszkowski Simple Model with Noise')
# plt.legend()
# plt.grid(True)
# plt.show()