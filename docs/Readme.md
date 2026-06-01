# Baseball Dashboard

A data-driven Flask dashboard application that visualizes baseball statistics and team performance metrics. This Helm chart bootstraps a scalable deployment of the Baseball Dashboard stack on a Kubernetes cluster, featuring dynamic infrastructure scaling, dynamic authentication, and a built-in automated health-monitoring CronJob.

## Prerequisites

- Kubernetes 1.22+
- Helm v3.0.0+
- A running Kubernetes cluster (e.g., Minikube, EKS, GKE)

## TL;DR

```bash
helm repo add baseball-dash https://lgidon.github.io/Baseball/
helm repo update
helm install my-dashboard baseball-dash/baseball-dash --set adminPassword="SecurePassword123!" --set flaskSecretKey="CryptoKeyString" --version 0.2.1
