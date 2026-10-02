#!/bin/bash
# One-shot redeploy of Hop 24 onto the team cluster from the VM:  curl -sL https://raw.githubusercontent.com/vnmoorthy/hop24/main/deploy.sh | bash
set -e
export KUBECONFIG=${KUBECONFIG:-/config/team-10-k8s.yaml} PATH=$HOME/.local/bin:$PATH
NS=${NS:-team-10}; HOST=${HOST:-http://video-lab-team-10.cosmos.vastdata.com}
cd ~ && rm -rf hop24 && git clone -q https://github.com/vnmoorthy/hop24.git
DEP=$(kubectl -n $NS get ingress -o json | python3 -c "import sys,json;[print(p['backend']['service']['name']) for i in json.load(sys.stdin)['items'] for r in i['spec']['rules'] for p in r['http']['paths'] if p['path'].startswith('/app')]" | head -1)
CM=$(kubectl -n $NS get deploy "$DEP" -o jsonpath='{.spec.template.spec.volumes[0].configMap.name}')
echo "deployment=$DEP configmap=$CM"
cd ~/hop24/tools/hop24
kubectl -n $NS create configmap "$CM" $(for f in main.py index.html sprite.png blood.png policy.json masks__*.json; do printf -- "--from-file=%s " "$f"; done) --dry-run=client -o yaml | kubectl apply -f -
kubectl -n $NS rollout restart deploy/"$DEP"
kubectl -n $NS rollout status deploy/"$DEP" --timeout=180s
sleep 5
curl -s $HOST/app/health; echo
curl -s -o /dev/null -w "policy %{http_code} sprite %{http_code}\n" $HOST/app/policy.json $HOST/app/sprite.png
echo DEPLOY-DONE
